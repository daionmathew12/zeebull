import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), "ResortApp"))
load_dotenv(os.path.join(os.getcwd(), "ResortApp", ".env"))

engine = create_engine(os.getenv("DATABASE_URL"))

room_id = 2 # Room 101

with engine.connect() as conn:
    print(f"--- ALL Bookings for Room 101 (ID: {room_id}) ---")
    # Check regular bookings
    res = conn.execute(text("""
        SELECT b.id, b.guest_name, b.status, b.check_in, b.check_out
        FROM bookings b
        JOIN booking_rooms br ON b.id = br.booking_id
        WHERE br.room_id = :room_id
        ORDER BY b.id DESC LIMIT 5
    """), {"room_id": room_id})
    for row in res:
        print(f"Regular Booking - ID: {row.id}, Guest: {row.guest_name}, Status: {row.status}, In: {row.check_in}, Out: {row.check_out}")

    # Check package bookings
    res = conn.execute(text("""
        SELECT pb.id, pb.guest_name, pb.status, pb.check_in, pb.check_out
        FROM package_bookings pb
        JOIN package_booking_rooms pbr ON pb.id = pbr.package_booking_id
        WHERE pbr.room_id = :room_id
        ORDER BY pb.id DESC LIMIT 5
    """), {"room_id": room_id})
    for row in res:
        print(f"Package Booking - ID: {row.id}, Guest: {row.guest_name}, Status: {row.status}, In: {row.check_in}, Out: {row.check_out}")
