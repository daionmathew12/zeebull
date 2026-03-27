from sqlalchemy import create_engine, text
engine = create_engine('postgresql+psycopg2://postgres:qwerty123@localhost:5432/orchiddb')
with engine.connect() as conn:
    # Check all bookings that ever used room 101
    res = conn.execute(text("""
        SELECT b.id, b.status, b.guest_name, b.check_in, b.check_out, b.checked_in_at
        FROM bookings b
        JOIN booking_rooms br ON b.id = br.booking_id
        WHERE br.room_id = 2
        ORDER BY b.id DESC
    """))
    print("Booking History for Room 101 (Regular):")
    for r in res:
        print(dict(r._mapping))

    # Check all package bookings for room 101
    res = conn.execute(text("""
        SELECT pb.id, pb.status, pb.guest_name, pb.check_in, pb.check_out
        FROM package_bookings pb
        JOIN package_booking_rooms pbr ON pb.id = pbr.package_booking_id
        WHERE pbr.room_id = 2
        ORDER BY pb.id DESC
    """))
    print("\nPackage Booking History for Room 101:")
    for r in res:
        print(dict(r._mapping))

    # Check the room status again
    res = conn.execute(text("SELECT * FROM rooms WHERE id = 2"))
    print("\nCurrent Room 101 data:")
    print(dict(res.fetchone()._mapping))
