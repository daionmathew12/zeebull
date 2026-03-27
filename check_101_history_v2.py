from sqlalchemy import create_engine, text
import json
import datetime

def json_serial(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

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
    history = [dict(r._mapping) for r in res]
    print("Booking History for Room 101 (Regular):")
    print(json.dumps(history, default=json_serial, indent=2))

    # Check all package bookings for room 101
    res = conn.execute(text("""
        SELECT pb.id, pb.status, pb.guest_name, pb.check_in, pb.check_out
        FROM package_bookings pb
        JOIN package_booking_rooms pbr ON pb.id = pbr.package_booking_id
        WHERE pbr.room_id = 2
        ORDER BY pb.id DESC
    """))
    p_history = [dict(r._mapping) for r in res]
    print("\nPackage Booking History for Room 101:")
    print(json.dumps(p_history, default=json_serial, indent=2))

    # Check the room status again
    res = conn.execute(text("SELECT * FROM rooms WHERE id = 2"))
    room_data = dict(res.fetchone()._mapping)
    print("\nCurrent Room 101 data:")
    print(json.dumps(room_data, default=json_serial, indent=2))
