import os
import sys
# Add current directory to path
sys.path.append(os.getcwd())

print("Script started")

from app.database import SessionLocal
from app.models.booking import Booking, PackageBooking
from datetime import date

print("Imports successful")

db = SessionLocal()
try:
    today = date(2026, 4, 22)
    print(f"Checking bookings for {today}")
    
    room_bookings = db.query(Booking).all()
    print(f"Total Room Bookings in DB: {len(room_bookings)}")
    
    package_bookings = db.query(PackageBooking).all()
    print(f"Total Package Bookings in DB: {len(package_bookings)}")
    
    today_rooms = [b for b in room_bookings if b.check_in_date == today]
    print(f"Room Bookings checking in today: {len(today_rooms)}")
    
    today_packages = [b for b in package_bookings if b.check_in_date == today]
    print(f"Package Bookings checking in today: {len(today_packages)}")

except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
    print("Script finished")
