from sqlalchemy import create_engine, text
engine = create_engine('postgresql+psycopg2://postgres:qwerty123@localhost:5432/orchiddb')
with engine.connect() as conn:
    # Update room 101 status to Available
    conn.execute(text("UPDATE rooms SET status = 'Available' WHERE id = 2"))
    conn.commit()
    print("Room 101 status updated to Available.")
