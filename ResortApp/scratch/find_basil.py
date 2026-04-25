from app.database import SessionLocal
from app.models.booking import Booking
from app.models.Package import PackageBooking

db = SessionLocal()
try:
    bookings = db.query(Booking).filter(Booking.guest_name.ilike("%Basil%")).all()
    for b in bookings:
        print(f"Regular Booking ID: {b.id}, Name: {b.guest_name}, Status: {b.status}")
        
    p_bookings = db.query(PackageBooking).filter(PackageBooking.guest_name.ilike("%Basil%")).all()
    for b in p_bookings:
        print(f"Package Booking ID: {b.id}, Name: {b.guest_name}, Status: {b.status}")
finally:
    db.close()
