from app.database import SessionLocal
from app.models.room import Room
from app.models.booking import Booking, BookingRoom
from app.models.Package import PackageBooking, PackageBookingRoom
from sqlalchemy.orm import joinedload

def reproduce_active_rooms():
    db = SessionLocal()
    print("=== Reproducing Active Rooms Query ===")
    
    # Copying query exactly from get_active_rooms
    active_bookings = (db.query(Booking)
                       .options(
                           joinedload(Booking.booking_rooms).joinedload(BookingRoom.room)
                       )
                       .filter(Booking.status.in_(['checked-in', 'checked_in', 'booked']))
                       .order_by(Booking.id.desc())
                       .all())
                       
    print(f"Active Bookings Count: {len(active_bookings)}")
    
    for b in active_bookings:
        print(f"Booking {b.id} | Status: '{b.status}'")
        for br in b.booking_rooms:
            r_num = br.room.number if br.room else "None"
            print(f"  - Room {r_num} (Status: {br.room.status if br.room else 'N/A'})")
            if r_num == '103':
                print("  !!! FOUND ROOM 103 IN ACTIVE BOOKING !!!")
                
    db.close()

if __name__ == "__main__":
    reproduce_active_rooms()
