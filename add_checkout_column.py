from sqlalchemy import create_engine, text
engine = create_engine('postgresql+psycopg2://postgres:qwerty123@localhost:5432/orchiddb')
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE bookings ADD COLUMN checked_out_at TIMESTAMP WITHOUT TIME ZONE"))
        print("Added checked_out_at to bookings")
    except Exception as e:
        print(f"Bookings error: {e}")
    
    try:
        conn.execute(text("ALTER TABLE package_bookings ADD COLUMN checked_out_at TIMESTAMP WITHOUT TIME ZONE"))
        print("Added checked_out_at to package_bookings")
    except Exception as e:
        print(f"Package bookings error: {e}")
    
    conn.commit()
