import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), "ResortApp"))
load_dotenv(os.path.join(os.getcwd(), "ResortApp", ".env"))

engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    # Check Room 101 (likely number 101)
    res = conn.execute(text("SELECT id, number, type, status, branch_id FROM rooms WHERE number = '101'"))
    for row in res:
        print(f"Room: ID={row.id}, Number={row.number}, Type={row.type}, Status={row.status}, Branch={row.branch_id}")
        
    # Check active bookings for Room 101
    room_id = row.id if 'row' in locals() else 2 # Assuming 101 has ID 2 based on previous context
    print(f"Checking bookings for Room ID: {room_id}")
    
    res = conn.execute(text("""
        SELECT b.id, b.guest_name, b.status 
        FROM bookings b
        JOIN booking_rooms br ON b.id = br.booking_id
        WHERE br.room_id = :room_id AND b.status NOT IN ('cancelled', 'checked_out')
    """), {"room_id": room_id})
    for row in res:
        print(f"Active Booking: ID={row.id}, Guest={row.guest_name}, Status={row.status}")

    res = conn.execute(text("""
        SELECT pb.id, pb.guest_name, pb.status
        FROM package_bookings pb
        JOIN package_booking_rooms pbr ON pb.id = pbr.package_booking_id
        WHERE pbr.room_id = :room_id AND pb.status NOT IN ('cancelled', 'checked_out')
    """), {"room_id": room_id})
    for row in res:
        print(f"Active Package Booking: ID={row.id}, Guest={row.guest_name}, Status={row.status}")
