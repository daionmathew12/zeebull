import os
import sys

# Suppress Pyre2 false positive warnings about SQLAlchemy model typing
import warnings
with warnings.catch_warnings():
    warnings.simplefilter('ignore')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.room import Room
from app.models.booking import Booking, BookingRoom
from sqlalchemy.orm import joinedload

def inspect_room_101():
    db = SessionLocal()
    try:
        print("====== Room 101 Inspection ======")
        room = db.query(Room).filter(Room.room_number == '101').first()
        
        if not room:
            print("❌ Room 101 not found in database!")
            return
            
        print(f"Room 101 ID: {room.id}")
        print(f"Room 101 Status: '{room.status}' (Raw value: {repr(room.status)})")
        
        print("\n--- Active Bookings attached to Room 101 ---")
        active_bookings = db.query(BookingRoom).options(
            joinedload(BookingRoom.booking)
        ).filter(
            BookingRoom.room_id == room.id
        ).all()
        
        found_active = False
        for br in active_bookings:
            if br.booking.status in ['checked_in', 'confirmed']:
                found_active = True
                print(f"  [ACTIVE] Booking ID: {br.booking.id} | Display ID: {br.booking.display_id}")
                print(f"           Status: {br.booking.status} | Guest: {br.booking.guest_name}")
            else:
                print(f"  [INACTIVE] Booking ID: {br.booking.id} | Display ID: {br.booking.display_id} | Status: {br.booking.status}")
                
        if not found_active:
            print("  (None found)")

        print("\n--- Investigating BK-000004 Status ---")
        target_bk = db.query(Booking).filter(Booking.display_id == 'BK-000004').first()
        
        if not target_bk:
            print("❌ Booking BK-000004 not found")
        else:
            print(f"Target BK-000004 ID: {target_bk.id}")
            print(f"Target Status: {target_bk.status}")
            print("Target Attached Rooms:")
            for br in target_bk.booking_rooms:
                r = db.query(Room).filter(Room.id == br.room_id).first()
                if r:
                    print(f"  Room {r.room_number} (ID: {r.id}, Status: {r.status})")
                else:
                    print(f"  Room ID {br.room_id} (Not Found in Rooms table)")
            
    except Exception as e:
        print(f"Error during inspection: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_room_101()
