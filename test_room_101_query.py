import uuid, shutil, os
from sqlalchemy import create_engine, or_, func
from sqlalchemy.orm import sessionmaker
from ResortApp.app.models.room import Room
from ResortApp.app.models.booking import Booking, BookingRoom
from ResortApp.app.database import SessionLocal

db = SessionLocal()

# Mock the check from check-in logic
booking = db.query(Booking).filter(Booking.id == 4).first()
if booking.booking_rooms:
    room_ids = [br.room_id for br in booking.booking_rooms]
    occupied_rooms = db.query(Room).filter(
        Room.id.in_(room_ids),
        or_(
            func.lower(Room.status) == 'checked-in',
            func.lower(Room.status) == 'occupied'
        )
    ).all()
    
    # Wait, the code in backend has a BUG or what?
    # Let's print out the exact values:
    all_rooms = db.query(Room).filter(Room.id.in_(room_ids)).all()
    for room in all_rooms:
        print(f"Room {room.number}: id={room.id}, status={room.status}, lower={room.status.lower() if room.status else None}")
        
    print(f"Occupied rooms found by query: {[r.number for r in occupied_rooms]}")
