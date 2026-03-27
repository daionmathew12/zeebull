from app.utils.auth import get_db
from app.models.booking import Booking, BookingRoom
from app.models.room import Room
from app.api.booking import parse_display_id

db = next(get_db())

booking_id_str = "BK-000068"
numeric_id, _ = parse_display_id(booking_id_str)
print(f"Parsed ID: {numeric_id}")

booking = db.query(Booking).filter(Booking.id == numeric_id).first()

if not booking:
    print("Booking NOT FOUND")
else:
    print(f"Booking Status: '{booking.status}'")
    
    print("Rooms:")
    for br in booking.booking_rooms:
        room = br.room
        print(f" - Room {room.number} (ID: {room.id}), Status: '{room.status}'")
        
    is_occupied = room.status.lower() in ['checked-in', 'occupied']
    print(f"   Is Occupied Flag: {is_occupied}")
    
    if is_occupied:
        print("Checking who is occupying Room 101...")
        active_booking = db.query(Booking).join(BookingRoom).filter(
            BookingRoom.room_id == room.id,
            Booking.status == 'checked-in'
        ).first()
        
        if active_booking:
            print(f"Room 101 is occupied by Booking {active_booking.id} ({active_booking.guest_name})")
        else:
            print("Room 101 has status 'Occupied' but NO 'checked-in' booking found! (Phantom Status)")
            print("FIXING STATUS: Setting Room 101 to 'Booked' so Check-In can proceed...")
            room.status = 'Booked'
            db.commit()
            print("Status updated to 'Booked'.")
