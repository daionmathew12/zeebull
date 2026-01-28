
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

# Use the connection string from .env or default to local sqlite/postgres
# In this environment, it seems to be postgres usually, but let's check .env
# The user's .env had sqlite, but reset_asvc1.py had postgres.
# I'll try the postgres one first as it's more likely for production-like checkout.
DATABASE_URL = "postgresql://orchid_user:admin123@localhost/orchid_resort"

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        # Check bookings
        result = connection.execute(text("SELECT id, guest_name, total_amount, check_in, check_out, status FROM bookings ORDER BY id DESC LIMIT 5"))
        print("\n--- Recent Bookings ---")
        for row in result:
            print(f"ID: {row.id}, Guest: {row.guest_name}, Amount: {row.total_amount}, Dates: {row.check_in} to {row.check_out}, Status: {row.status}")
            
            # Check rooms for this booking
            rooms_result = connection.execute(text(f"""
                SELECT r.id, r.number, r.price 
                FROM booking_rooms br 
                JOIN rooms r ON br.room_id = r.id 
                WHERE br.booking_id = {row.id}
            """))
            print(f"  Rooms:")
            for room in rooms_result:
                print(f"    - Room {room.number} (ID: {room.id}), Price: {room.price}")

except Exception as e:
    print(f"Error connecting to DB: {e}")
