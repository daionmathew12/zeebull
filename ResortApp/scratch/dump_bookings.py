import requests
import json

BASE_URL = "http://localhost:8011/api"

def check_data():
    try:
        # We need a token. I'll try to find one from existing logs or env.
        # But for local dev, maybe I can just query the DB.
        # Actually, let's just use the DB query I wrote earlier, but make it more thorough.
        pass
    except Exception as e:
        print(f"Error: {e}")

from app.database import SessionLocal
from app.models.booking import Booking, PackageBooking
from datetime import date

db = SessionLocal()
try:
    print("--- ROOM BOOKINGS ---")
    bookings = db.query(Booking).all()
    for b in bookings:
        print(f"ID: {b.id}, Guest: {b.guest_name}, Check-in: {b.check_in}, Status: {b.status}")
    
    print("\n--- PACKAGE BOOKINGS ---")
    p_bookings = db.query(PackageBooking).all()
    for b in p_bookings:
        print(f"ID: {b.id}, Guest: {b.guest_name}, Check-in: {b.check_in}, Status: {b.status}")

finally:
    db.close()
