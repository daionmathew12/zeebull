
from sqlalchemy import create_engine, text
import os

DATABASE_URL = "postgresql://orchiduser:orchid123@localhost:5432/orchiddb"

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as connection:
        print("\n=== CHECKING LATEST BOOKINGS ===")
        # Check bookings
        result = connection.execute(text("SELECT id, guest_name, total_amount, check_in, check_out, status FROM bookings ORDER BY id DESC LIMIT 5"))
        for row in result:
            print(f"Booking ID: {row.id}")
            print(f"  Guest: {row.guest_name}")
            print(f"  Total Amount: {row.total_amount}")
            print(f"  Dates: {row.check_in} to {row.check_out}")
            print(f"  Status: {row.status}")
            
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
            print("-" * 30)

except Exception as e:
    print(f"Error connecting to DB: {e}")
