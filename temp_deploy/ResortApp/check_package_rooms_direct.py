from app.database import SessionLocal
from app.models.Package import PackageBookingRoom
from app.models.room import Room
import sys

def check_package_rooms_direct():
    db = SessionLocal()
    print("=== Checking Package Rooms Direct ===")
    
    links = db.query(PackageBookingRoom).filter(PackageBookingRoom.package_booking_id == 1).all()
    print(f"Found {len(links)} links for Package Booking 1")
    
    for link in links:
        if link.room:
            print(f"  - Room {link.room.number} (ID: {link.room_id})")
        else:
            print(f"  - Link {link.id} Room ID {link.room_id} -> Room NOT loaded")
            
    db.close()
    sys.stdout.flush()

if __name__ == "__main__":
    check_package_rooms_direct()
