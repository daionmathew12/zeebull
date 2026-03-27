from sqlalchemy import create_engine, text
import sys

DATABASE_URL = "postgresql+psycopg2://postgres:qwerty123@localhost:5432/orchiddb"

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Connected to database.")
        
        # Room Status
        res = conn.execute(text("SELECT id, number, status FROM rooms WHERE number = '101'")).fetchone()
        if res:
            room_id = res[0]
            print(f"Room 101: ID={room_id}, Number={res[1]}, Status={res[2]}")
            
            # ALL Bookings history
            print("\n--- Standard Bookings history (Last 5) ---")
            bookings = conn.execute(text("""
                SELECT b.id, b.status, b.check_in, b.check_out, b.created_at
                FROM bookings b 
                JOIN booking_rooms br ON b.id = br.booking_id 
                WHERE br.room_id = :rid 
                ORDER BY b.created_at DESC LIMIT 5
            """), {"rid": room_id}).fetchall()
            for b in bookings:
                print(b)
                
            # ALL Package Bookings history
            print("\n--- Package Bookings history (Last 5) ---")
            pb = conn.execute(text("""
                SELECT pb.id, pb.status, pb.check_in, pb.check_out, pb.created_at
                FROM package_bookings pb 
                JOIN package_booking_rooms pbr ON pb.id = pbr.package_booking_id 
                WHERE pbr.room_id = :rid 
                ORDER BY pb.created_at DESC LIMIT 5
            """), {"rid": room_id}).fetchall()
            for p in pb:
                print(p)
                
            # Check for ANY checked-in status in room_status field of rooms table
            # Some versions might use a different field. Let's check columns for rooms.
            print("\n--- Room Table columns check ---")
            cols = conn.execute(text("""
                SELECT column_name FROM information_schema.columns WHERE table_name = 'rooms';
            """)).fetchall()
            for c in cols:
                print(c[0])

        else:
            print("Room 101 not found.")
except Exception as e:
    print(f"Error: {e}")

sys.stdout.flush()
