from sqlalchemy.orm import Session
from datetime import date, timedelta
import logging

from app.database import SessionLocal
from app.models.room import RoomType, Room
from app.models.booking import Booking, BookingRoom
from app.core.aiosell_client import push_inventory, push_rate, batch_push_inventory

logger = logging.getLogger(__name__)

def _calculate_availability_for_date(db: Session, room_type_id: int, target_date: date, branch_id: int = 1) -> int:
    """Calculates exactly how many rooms of a type are open on a given night"""
    
    room_type = db.query(RoomType).filter(RoomType.id == room_type_id).first()
    if not room_type: return 0
    
    # 1. Total rooms of this type
    total_physical = db.query(Room).filter(
        Room.room_type_id == room_type_id, 
        Room.branch_id == branch_id,
        Room.status != "Deleted"
    ).count()
    
    # Base capacity is total_inventory if set, else physical
    capacity = room_type.total_inventory if (room_type.total_inventory and room_type.total_inventory > 0) else total_physical
    
    # 2. Hard allocations on that date
    assigned_overlaps = db.query(BookingRoom).join(Booking).join(Room).filter(
        Room.room_type_id == room_type_id,
        Booking.branch_id == branch_id,
        Booking.status.in_(["Booked", "Checked-in", "Confirmed"]),
        Booking.check_in <= target_date,
        Booking.check_out > target_date
    ).count()
    
    # 3. Soft allocations
    from sqlalchemy import func
    soft_overlaps_sum = db.query(func.sum(Booking.num_rooms)).filter(
        Booking.room_type_id == room_type_id,
        Booking.branch_id == branch_id,
        Booking.status.in_(["Booked", "Confirmed"]),
        Booking.check_in <= target_date,
        Booking.check_out > target_date,
        ~Booking.booking_rooms.any()
    ).scalar()
    
    soft_overlaps = int(soft_overlaps_sum) if soft_overlaps_sum else 0
    
    available = capacity - (assigned_overlaps + soft_overlaps)
    return max(0, available)


def trigger_inventory_push(room_type_id: int, days: int = 30):
    """
    Calculates availability and PUSHES directly to Aiosell.
    Designed to be run as a BackgroundTask.
    """
    db = SessionLocal()
    try:
        room_type = db.query(RoomType).filter(RoomType.id == room_type_id).first()
        if not room_type:
            print(f"[AIOSELL DEBUG] Inventory Push aborted: RoomType {room_type_id} not found")
            return
            
        if not room_type.channel_manager_id:
            print(f"[AIOSELL DEBUG] Inventory Push aborted: RoomType {room_type.name} has no CM mapping")
            return
            
        print(f"[AIOSELL DEBUG] Starting Inventory Push for {room_type.name} ({room_type.channel_manager_id})")
        
        start_date = date.today()
        batch_data = []
        
        for i in range(days):
            target_date = start_date + timedelta(days=i)
            available = _calculate_availability_for_date(db, room_type_id, target_date)
            
            batch_data.append({
                "room_code": room_type.channel_manager_id,
                "qty": available,
                "start_date": target_date,
                "end_date": target_date
            })
            
        if batch_data:
            success = batch_push_inventory(batch_data)
            status = "SUCCESS" if success else "FAILED"
            print(f"[AIOSELL DEBUG] Inventory Push {status} for {room_type.name}")
            logger.info(f"[AIOSELL TRIGGER] Pushed inventory for {room_type.name} ({room_type.channel_manager_id}) for {days} days. Result: {status}")
    except Exception as e:
        print(f"[AIOSELL ERROR] trigger_inventory_push failed: {e}")
        logger.error(f"Aiosell inventory trigger error: {e}")
    finally:
        db.close()


def trigger_rates_push(room_type_id: int):
    """
    Pushes current base_price for next 1 year DIRECTLY to Aiosell.
    Designed to be run as a BackgroundTask.
    """
    db = SessionLocal()
    try:
        room_type = db.query(RoomType).filter(RoomType.id == room_type_id).first()
        if not room_type:
            print(f"[AIOSELL DEBUG] Rates Push aborted: RoomType {room_type_id} not found")
            return
            
        if not room_type.channel_manager_id:
            print(f"[AIOSELL DEBUG] Rates Push aborted: RoomType {room_type.name} has no CM mapping")
            return
            
        print(f"[AIOSELL DEBUG] Starting Rate Push for {room_type.name} ({room_type.channel_manager_id}) @ {room_type.base_price}")
        
        start = date.today()
        end = start + timedelta(days=365)
        
        # Rate Plan ID format as provided by Aiosell: e.g. EXECUTIVE-S-101
        rate_plan_id = f"{room_type.channel_manager_id}-S-101"

        success = push_rate(
            room_code=room_type.channel_manager_id,
            base_price=room_type.base_price,
            start_date=start,
            end_date=end,
            rate_plan_code=rate_plan_id
        )
        status = "SUCCESS" if success else "FAILED"
        print(f"[AIOSELL DEBUG] Rate Push {status} for {room_type.name}")
        logger.info(f"[AIOSELL TRIGGER] Pushed rates for {room_type.name} at {room_type.base_price}. Result: {status}")
    except Exception as e:
        print(f"[AIOSELL ERROR] trigger_rates_push failed: {e}")
        logger.error(f"Aiosell rates trigger error: {e}")
    finally:
        db.close()


def trigger_restrictions_push(room_type_id: int, stop_sell: bool = False, min_stay: int = None, max_stay: int = None):
    """
    Pushes Stop Sell and other restrictions directly to Aiosell.
    Designed to be run as a BackgroundTask.
    """
    db = SessionLocal()
    try:
        room_type = db.query(RoomType).filter(RoomType.id == room_type_id).first()
        if not room_type:
            print(f"[AIOSELL DEBUG] Restriction Push aborted: RoomType {room_type_id} not found")
            return
            
        if not room_type.channel_manager_id:
            print(f"[AIOSELL DEBUG] Restriction Push aborted: RoomType {room_type.name} has no CM mapping")
            return
            
        print(f"[AIOSELL DEBUG] Starting Restriction Push for {room_type.name} ({room_type.channel_manager_id}), StopSell={stop_sell}")
        
        from app.core.aiosell_client import push_restriction
        start = date.today()
        # Push restrictions for the next 1 year by default (or as per requirements)
        end = start + timedelta(days=365)
        
        success = push_restriction(
            room_code=room_type.channel_manager_id,
            start_date=start,
            end_date=end,
            stop_sell=stop_sell,
            min_stay=min_stay,
            max_stay=max_stay
        )
        status = "SUCCESS" if success else "FAILED"
        print(f"[AIOSELL DEBUG] Restriction Push {status} for {room_type.name}")
        logger.info(f"[AIOSELL TRIGGER] Pushed restrictions for {room_type.name}. StopSell={stop_sell}. Result: {status}")
    except Exception as e:
        print(f"[AIOSELL ERROR] trigger_restrictions_push failed: {e}")
        logger.error(f"Aiosell restriction trigger error: {e}")
    finally:
        db.close()
