from app.database import SessionLocal
from app.models.Package import PackageBooking, PackageBookingRoom
from app.models.room import Room
from sqlalchemy.orm import joinedload

def check_package_rooms():
    db = SessionLocal()
    print("=== Checking Package Booking 1 Rooms ===")
    
    pb = (db.query(PackageBooking)
          .options(
              joinedload(PackageBooking.rooms).joinedload(PackageBookingRoom.room)
          )
          .filter(PackageBooking.id == 1)
          .first())
          
    if not pb:
        print("Package Booking 1 not found")
    else:
        print(f"Package Booking {pb.id} | Status: {pb.status}")
        print(f"Rooms Count: {len(pb.rooms)}")
        for pbr in pb.rooms:
            room = pbr.room
            if room:
                print(f"  - Room {room.number} (ID: {room.id}) | Status: {room.status}")
            else:
                print(f"  - Room Link ID {pbr.id} has no Room Object")
                
    db.close()

if __name__ == "__main__":
    check_package_rooms()
