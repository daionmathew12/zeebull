from app.database import SessionLocal
from app.api.booking import get_booking_details
import json

db = SessionLocal()
try:
    # Simulate the API call for Booking 6
    # We need to mock the 'current_user' if it's used, but let's see if we can call it.
    # Actually get_booking_details is a route function.
    # Let's just manually perform the logic from it for Booking 6.
    from app.models.booking import Booking
    from sqlalchemy.orm import joinedload
    from app.models.booking import BookingRoom
    from app.models.user import User
    
    booking_id = 6
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    
    if not booking:
        print("Booking 6 not found")
    else:
        # Get room IDs
        room_ids = [r.room_id for r in booking.booking_rooms if r.room_id]
        print(f"Booking {booking_id} rooms: {room_ids}")
        
        from app.api.booking import _fetch_inventory, _fetch_extras, _fetch_services
        
        start_filter = booking.checked_in_at or booking.check_in
        inventory = _fetch_inventory(db, room_ids, start_filter, booking.check_out, booking_id=booking.id)
        
        print(f"Inventory usage count: {len(inventory)}")
        for item in inventory:
            print(f" - {item['item_name']} (Asset: {item.get('is_asset_fixed')}, Type: {item.get('type')})")

finally:
    db.close()
