from app.database import SessionLocal
from app.models.booking import Booking, BookingRoom
from app.models.Package import PackageBooking, PackageBookingRoom
from app.models.room import Room
from sqlalchemy.orm import joinedload

db = SessionLocal()
try:
    booking = db.query(Booking).options(joinedload(Booking.booking_rooms).joinedload(BookingRoom.room)).filter(Booking.id == 7).first()
    if booking:
        print(f"Regular Booking {booking.id} ({booking.guest_name})")
        for br in booking.booking_rooms:
            if br.room: print(f"  Room ID: {br.room.id}, Number: {br.room.number}")
            else: print(f"  Room ID: {br.room_id}, Room object is NULL")
    else:
        print("Regular Booking 7 not found")

    p_booking = db.query(PackageBooking).options(joinedload(PackageBooking.rooms).joinedload(PackageBookingRoom.room)).filter(PackageBooking.id == 7).first()
    if p_booking:
        print(f"Package Booking {p_booking.id} ({p_booking.guest_name})")
        for r in p_booking.rooms:
            if r.room: print(f"  Room ID: {r.room.id}, Number: {r.room.number}")
            else: print(f"  Room ID: {r.room_id}, Room object is NULL")
    else:
        print("Package Booking 7 not found")
finally:
    db.close()
