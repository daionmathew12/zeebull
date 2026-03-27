from app.database import SessionLocal
from app.models.room import Room
from app.models.booking import Booking, BookingRoom
from app.models.Package import PackageBooking, PackageBookingRoom

def check_db():
    db = SessionLocal()
    print("=== Checking Active Rooms Logic ===")
    
    # Check specific rooms mentioned by user
    target_rooms = ['103', '001']
    
    for r_num in target_rooms:
        print(f"\n--- Room {r_num} ---")
        room = db.query(Room).filter(Room.number == r_num).first()
        if not room:
            print(f"Room {r_num} not found!")
            continue
            
        print(f"Room Status: {room.status}")
        
        # Check active bookings
        bookings = (db.query(Booking)
                    .join(BookingRoom)
                    .filter(BookingRoom.room_id == room.id)
                    .order_by(Booking.id.desc())
                    .limit(3)
                    .all())
                    
        for b in bookings:
            print(f"Booking ID: {b.id} | Status: {b.status} | Guest: {b.guest_name} | CheckOut: {b.check_out}")
            
        # Check active package bookings
        pkg_bookings = (db.query(PackageBooking)
                        .join(PackageBookingRoom)
                        .filter(PackageBookingRoom.room_id == room.id)
                        .order_by(PackageBooking.id.desc())
                        .limit(3)
                        .all())
                        
        for pb in pkg_bookings:
            print(f"Pkg Booking ID: {pb.id} | Status: {pb.status} | CheckOut: {pb.check_out}")

    db.close()

if __name__ == "__main__":
    check_db()
