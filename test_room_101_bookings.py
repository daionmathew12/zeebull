from sqlalchemy import create_engine, text
engine = create_engine('postgresql+psycopg2://postgres:qwerty123@localhost:5432/orchiddb')
with engine.connect() as conn:
    res = conn.execute(text("SELECT * FROM bookings b JOIN booking_rooms br ON br.booking_id = b.id WHERE br.room_id = 2 AND b.status IN ('booked', 'checked-in')"))
    print("Bookings for Room 2 (101):", [dict(r._mapping) for r in res])
