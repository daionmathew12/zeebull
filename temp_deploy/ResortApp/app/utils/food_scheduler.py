import asyncio
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from app.database import SessionLocal
from app.models.Package import PackageBooking
from app.models.foodorder import FoodOrder, FoodOrderItem
from app.models.service_request import ServiceRequest
from app.models.room import Room
from app.curd.foodorder import trigger_scheduled_orders, create_food_order
from app.schemas.foodorder import FoodOrderCreate, FoodOrderItemCreate

def get_ist_time():
    """Get current time in Indian Standard Time"""
    # Assuming the server might be in UTC, IST is UTC+5:30
    return datetime.utcnow() + timedelta(hours=5, minutes=30)

async def run_food_scheduler():
    """Background task to check food schedules every minute"""
    print("[SCHEDULER] Starting food schedule monitor (IST)...")
    while True:
        try:
            check_food_schedules()
        except Exception as e:
            print(f"[SCHEDULER] Error: {e}")
            import traceback
            traceback.print_exc()
        
        # Wait for next minute check
        await asyncio.sleep(60) 

def check_food_schedules():
    db = SessionLocal()
    try:
        now_ist = get_ist_time()
        
        # 1. Trigger individual scheduled FoodOrders
        try:
            trigger_scheduled_orders(db)
        except Exception as e:
            print(f"[SCHEDULER] Error triggering individual orders: {e}")

        # 2. Handle recurring Package Meals
        # Lookahead for 60 minutes
        target_time = now_ist + timedelta(minutes=60)
        target_time_str = target_time.strftime("%H:%M") # e.g. "08:00"
        
        # Get active checked-in bookings
        active_bookings = (
            db.query(PackageBooking)
            .options(joinedload(PackageBooking.package))
            .options(joinedload(PackageBooking.rooms))
            .filter(PackageBooking.status.in_(['checked-in', 'checked_in']))
            .all()
        )
        
        count = 0
        for booking in active_bookings:
            if not booking.package or not booking.package.food_timing:
                continue
                
            try:
                timings_data = booking.package.food_timing
                timings = {}
                
                if isinstance(timings_data, str):
                    try:
                         timings_data = json.loads(timings_data)
                    except:
                         pass
                
                if isinstance(timings_data, dict):
                    timings = timings_data
                
                if not timings:
                    continue
                    
            except Exception as e:
                continue
                
            for meal, data in timings.items():
                scheduled_time = ""
                scheduled_items = []
                
                if isinstance(data, dict):
                    scheduled_time = data.get("time", "")
                    scheduled_items = data.get("items", [])
                else:
                    scheduled_time = str(data) 
                
                # Check if target time matches scheduled time
                if scheduled_time == target_time_str:
                    for room_link in booking.rooms:
                        room_id = room_link.room_id
                        
                        # Prevent duplicates for today
                        start_of_day = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
                        
                        # Check for existing FoodOrder for this meal today
                        exists = db.query(FoodOrder).filter(
                             FoodOrder.room_id == room_id,
                             FoodOrder.delivery_request.like(f"Auto-Scheduled {meal}%"),
                             FoodOrder.created_at >= start_of_day
                        ).first()
                        
                        if not exists:
                            print(f"[AUTO-SCHEDULER] Generating {meal} FoodOrder for Room {room_id} (Scheduled: {scheduled_time})")
                            
                            # Prepare items list
                            items_to_create = []
                            for item in scheduled_items:
                                if isinstance(item, dict) and item.get("id"):
                                    items_to_create.append(FoodOrderItemCreate(
                                        food_item_id=int(item["id"]),
                                        quantity=int(item.get("qty", 1))
                                    ))
                            
                            # Create Food Order
                            # amount=0 makes it complimentary
                            # order_type="room_service" triggers ServiceRequest creation in curd layer
                            order_data = FoodOrderCreate(
                                room_id=room_id,
                                amount=0.0,
                                assigned_employee_id=None,
                                items=items_to_create,
                                status="pending",
                                billing_status="unbilled",
                                order_type="room_service",
                                delivery_request=f"Auto-Scheduled {meal} for {scheduled_time} (Package: {booking.package.title})"
                            )
                            
                            try:
                                # This will also create the ServiceRequest because order_type="room_service"
                                create_food_order(db, order_data)
                                count += 1
                            except Exception as e:
                                print(f"[SCHEDULER] Failed to create food order: {e}")
                            
        if count > 0:
            print(f"[AUTO-SCHEDULER] Successfully generated {count} food orders for meal time {target_time_str}")
            
    except Exception as e:
        print(f"Error in check_food_schedules: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

