
from app.database import SessionLocal
from app.api.booking import _fetch_extras, _fetch_services, _fetch_inventory
from app.models.booking import Booking, BookingRoom
from sqlalchemy.orm import joinedload
import json

db = SessionLocal()
try:
    booking_id = 6
    booking = db.query(Booking).options(
        joinedload(Booking.booking_rooms).joinedload(BookingRoom.room)
    ).filter(Booking.id == booking_id).first()

    if not booking:
        print(f"Booking {booking_id} not found")
    else:
        room_ids = [br.room_id for br in booking.booking_rooms if br.room_id]
        start_filter = booking.checked_in_at or booking.check_in
        
        print(f"Booking ID: {booking.id}")
        print(f"Room IDs: {room_ids}")
        print(f"Start Filter (Date): {start_filter}")
        print(f"Check Out (Date): {booking.check_out}")

        food_orders = _fetch_extras(db, room_ids, start_filter, booking.check_out)
        service_requests = _fetch_services(db, room_ids, start_filter, booking.check_out)
        
        print("\n--- FOOD ORDERS ---")
        print(json.dumps(food_orders, indent=2, default=str))
        
        print("\n--- SERVICE REQUESTS ---")
        print(json.dumps(service_requests, indent=2, default=str))

        # Check ALL food orders for this booking directly
        from app.models.foodorder import FoodOrder
        all_fo = db.query(FoodOrder).filter(FoodOrder.booking_id == booking_id).all()
        print(f"\nTotal FoodOrders directly linked to booking_id {booking_id}: {len(all_fo)}")
        for fo in all_fo:
            print(f"  - ID: {fo.id}, RoomID: {fo.room_id}, CreatedAt: {fo.created_at}")

finally:
    db.close()
