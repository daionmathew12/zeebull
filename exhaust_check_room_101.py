import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), "ResortApp"))
load_dotenv(os.path.join(os.getcwd(), "ResortApp", ".env"))

engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("Checking ALL rooms...")
    res = conn.execute(text("SELECT id, number, status, branch_id FROM rooms"))
    for row in res:
        print(f"Room: ID={row.id}, No={row.number}, Status={row.status}, Branch={row.branch_id}")

    print("\nChecking ALL booking_rooms for room_id=2...")
    res = conn.execute(text("""
        SELECT br.booking_id, b.guest_name, b.status, b.check_in, b.check_out
        FROM booking_rooms br
        JOIN bookings b ON br.booking_id = b.id
        WHERE br.room_id = 2
    """))
    for row in res:
        print(f"Booking: ID={row.booking_id}, Guest={row.guest_name}, Status={row.status}, In={row.check_in}, Out={row.check_out}")

    print("\nChecking ALL package_booking_rooms for room_id=2...")
    res = conn.execute(text("""
        SELECT pbr.package_booking_id, pb.guest_name, pb.status, pb.check_in, pb.check_out
        FROM package_booking_rooms pbr
        JOIN package_bookings pb ON pbr.package_booking_id = pb.id
        WHERE pbr.room_id = 2
    """))
    for row in res:
        print(f"Pkg Booking: ID={row.package_booking_id}, Guest={row.guest_name}, Status={row.status}, In={row.check_in}, Out={row.check_out}")
