from app.database import SessionLocal
from app.models.room import Room
from app.models.booking import Booking, BookingRoom

def check_ghost_bookings():
    db = SessionLocal()
    print("=== Checking Ghost Bookings for Room 103 ===")
    
    room = db.query(Room).filter(Room.number == '103').first()
    if not room:
        print("Room 103 not found")
        return

    # Check for ANY active booking
    active_bookings = (db.query(Booking)
                       .join(BookingRoom)
                       .filter(BookingRoom.room_id == room.id, 
                               Booking.status.in_(['checked-in', 'checked_in', 'booked']))
                       .all())
                       
    print(f"Found {len(active_bookings)} active bookings for Room 103:")
    for b in active_bookings:
        print(f"  ID: {b.id} | Status: {b.status} | Guest: {b.guest_name}")
        
    db.close()

if __name__ == "__main__":
    check_ghost_bookings()
