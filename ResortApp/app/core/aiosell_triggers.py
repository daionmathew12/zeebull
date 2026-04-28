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


def trigger_rates_push(room_type_id: int, days: int = 90):
    """
    Pushes dynamic rates for the next X days DIRECTLY to Aiosell.
    Considers:
    1. Base Price
    2. Weekend Price (Fri/Sat nights)
    3. Holiday/Long Weekend overrides from Pricing Calendar
    """
    db = SessionLocal()
    try:
        from app.models.room import RatePlan
        from app.models.calendar import PricingCalendar
        from app.core.aiosell_client import batch_push_rates
        
        room_type = db.query(RoomType).filter(RoomType.id == room_type_id).first()
        if not room_type:
            print(f"[AIOSELL DEBUG] Rates Push aborted: RoomType {room_type_id} not found")
            return
            
        if not room_type.channel_manager_id:
            print(f"[AIOSELL DEBUG] Rates Push aborted: RoomType {room_type.name} has no CM mapping")
            return

        # Fetch dynamic rate plans
        rate_plans = db.query(RatePlan).filter(RatePlan.room_type_id == room_type_id).all()
        if not rate_plans:
            # Fallback legacy logic if no dynamic plans exist
            rate_plans = [RatePlan(channel_manager_id=f"{room_type.channel_manager_id}-S-101", price_offset=0)]

        print(f"[AIOSELL DEBUG] Starting Dynamic Rate Push for {room_type.name} for {days} days")
        
        start_date = date.today()
        end_date = start_date + timedelta(days=days)
        
        # Fetch all pricing overrides for the range
        overrides = db.query(PricingCalendar).filter(
            PricingCalendar.end_date >= start_date,
            PricingCalendar.start_date <= end_date
        ).all()

        for plan in rate_plans:
            if not plan.channel_manager_id: continue
            
            batch_data = []
            current_rate = -1
            segment_start = None
            
            for i in range(days + 1):
                target_date = start_date + timedelta(days=i)
                
                # 1. Determine Day Type
                day_type = None
                for ov in overrides:
                    if ov.start_date <= target_date <= ov.end_date:
                        day_type = ov.day_type
                        break
                
                # 2. Calculate Daily Base for this RoomType
                if day_type == "HOLIDAY" and room_type.holiday_price:
                    daily_base = room_type.holiday_price
                elif day_type == "LONG_WEEKEND" and room_type.long_weekend_price:
                    daily_base = room_type.long_weekend_price
                elif day_type == "WEEKEND":
                    daily_base = room_type.weekend_price if room_type.weekend_price else (room_type.base_price or 0.0)
                elif day_type == "WEEKDAY":
                    daily_base = room_type.base_price or 0.0
                else:
                    # Default Weekend Logic: Friday (4) and Saturday (5)
                    is_weekend = target_date.weekday() in [4, 5]
                    if is_weekend and room_type.weekend_price:
                        daily_base = room_type.weekend_price
                    else:
                        daily_base = room_type.base_price or 0.0
                
                # 3. Apply Plan-specific logic
                if plan.base_price and plan.base_price > 0:
                    # Plan has a fixed price that overrides everything? 
                    # Usually offsets are better for dynamic pricing.
                    # If plan.base_price is set, we use it, but maybe we should still apply day-type?
                    # For now, let's assume if plan.base_price is set, it's a fixed rate.
                    rate = plan.base_price
                else:
                    rate = daily_base + (plan.price_offset or 0)

                # Group consecutive dates with same rate to minimize payload size
                if rate != current_rate:
                    if segment_start:
                        batch_data.append({
                            "room_code": room_type.channel_manager_id,
                            "rate": current_rate,
                            "start_date": segment_start,
                            "end_date": target_date - timedelta(days=1),
                            "rate_plan_code": plan.channel_manager_id
                        })
                    segment_start = target_date
                    current_rate = rate
            
            # Add final segment
            if segment_start:
                batch_data.append({
                    "room_code": room_type.channel_manager_id,
                    "rate": current_rate,
                    "start_date": segment_start,
                    "end_date": start_date + timedelta(days=days),
                    "rate_plan_code": plan.channel_manager_id
                })

            if batch_data:
                success = batch_push_rates(batch_data)
                status = "SUCCESS" if success else "FAILED"
                print(f"[AIOSELL DEBUG] Batch Rate Push {status} for Plan {plan.channel_manager_id}")
            
        logger.info(f"[AIOSELL TRIGGER] Pushed dynamic rates for {room_type.name} ({len(rate_plans)} plans) for {days} days")
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
