from app.database import SessionLocal
from app.models.booking import Booking
from app.models.room import Room
import json

def debug_checkin():
    db = SessionLocal()
    try:
        # Check Booking BK-000003
        b = db.query(Booking).filter(Booking.id == 3).first()
        if not b:
            print("Booking BK-000003 not found")
            return
            
        print(f"Booking: ID={b.id}, Status='{b.status}', Guest='{b.guest_name}'")
        
        # Check rooms for this booking
        from app.models.booking import BookingRoom
        rooms = db.query(Room).join(BookingRoom).filter(BookingRoom.booking_id == b.id).all()
        for r in rooms:
            print(f"Room: Number={r.number}, Status='{r.status}', LocationID={r.inventory_location_id}")
            if r.inventory_location_id:
                from app.models.inventory import Location
                loc = db.query(Location).filter(Location.id == r.inventory_location_id).first()
                print(f"  Location: ID={loc.id}, Type={loc.location_type if loc else 'N/A'}")
        
        # Check for Warehouse
        from app.models.inventory import Location
        warehouse = db.query(Location).filter(Location.location_type == "Warehouse").first()
        print(f"Warehouse found: {warehouse.id if warehouse else 'NONE'}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_checkin()
