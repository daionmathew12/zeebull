"""
Full investigation of Room 101 (ID=2) check-in blockage.
Checks all possible sources of stale state that could prevent check-in.
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv('ResortApp/.env')
DB_URL = os.getenv('DATABASE_URL')
engine = create_engine(DB_URL)

with engine.connect() as conn:
    print("=" * 60)
    print("ROOM 101 (ID=2) FULL INVESTIGATION")
    print("=" * 60)

    # 1. Room status
    print("\n[1] ROOM STATUS")
    r = conn.execute(text("SELECT id, number, status, type, branch_id FROM rooms WHERE id = 2")).fetchone()
    print(f"  Room: {dict(r._mapping)}")

    # 2. All bookings for room 2
    print("\n[2] ALL BOOKINGS for Room 2 (via booking_rooms)")
    rows = conn.execute(text("""
        SELECT b.id, b.display_id, b.guest_name, b.status, b.check_in, b.check_out,
               b.checked_in_at, b.checked_out_at
        FROM booking_rooms br
        JOIN bookings b ON br.booking_id = b.id
        WHERE br.room_id = 2
        ORDER BY b.id DESC
    """)).fetchall()
    for r in rows:
        print(f"  {dict(r._mapping)}")

    # 3. All package bookings for room 2
    print("\n[3] ALL PACKAGE BOOKINGS for Room 2 (via package_booking_rooms)")
    rows = conn.execute(text("""
        SELECT pb.id, pb.guest_name, pb.status, pb.check_in, pb.check_out,
               pb.checked_in_at, pb.checked_out_at
        FROM package_booking_rooms pbr
        JOIN package_bookings pb ON pbr.package_booking_id = pb.id
        WHERE pbr.room_id = 2
        ORDER BY pb.id DESC
    """)).fetchall()
    for r in rows:
        print(f"  {dict(r._mapping)}")
    if not rows:
        print("  (none)")

    # 4. Active bookings for room 2 (booked or checked-in)
    print("\n[4] ACTIVE BOOKINGS for Room 2 (booked or checked-in)")
    rows = conn.execute(text("""
        SELECT b.id, b.display_id, b.guest_name, b.status
        FROM booking_rooms br
        JOIN bookings b ON br.booking_id = b.id
        WHERE br.room_id = 2
          AND lower(b.status) IN ('booked', 'checked-in', 'checked_in')
    """)).fetchall()
    for r in rows:
        print(f"  ACTIVE REGULAR: {dict(r._mapping)}")
    
    rows = conn.execute(text("""
        SELECT pb.id, pb.guest_name, pb.status
        FROM package_booking_rooms pbr
        JOIN package_bookings pb ON pbr.package_booking_id = pb.id
        WHERE pbr.room_id = 2
          AND lower(pb.status) IN ('booked', 'checked-in', 'checked_in')
    """)).fetchall()
    for r in rows:
        print(f"  ACTIVE PACKAGE: {dict(r._mapping)}")
    
    if not rows:
        print("  (no active bookings)")

    # 5. Checkout records for room 101
    print("\n[5] CHECKOUT RECORDS for Room 101")
    rows = conn.execute(text("""
        SELECT id, booking_id, package_booking_id, room_number, checkout_date, status
        FROM checkouts
        WHERE room_number = '101'
        ORDER BY id DESC
    """)).fetchall()
    for r in rows:
        print(f"  {dict(r._mapping)}")
    if not rows:
        print("  (none)")

    # 6. All bookings with status 'booked' for room 2 - the one that wants to check in
    print("\n[6] BOOKINGS WITH 'booked' STATUS for Room 2 (ready to check in)")
    rows = conn.execute(text("""
        SELECT b.id, b.display_id, b.guest_name, b.status, b.check_in, b.check_out
        FROM booking_rooms br
        JOIN bookings b ON br.booking_id = b.id
        WHERE br.room_id = 2
          AND lower(b.status) = 'booked'
    """)).fetchall()
    for r in rows:
        print(f"  {dict(r._mapping)}")
    if not rows:
        print("  (no bookings with 'booked' status)")

    print("\n" + "=" * 60)
    print("INVESTIGATION COMPLETE")
    print("=" * 60)
