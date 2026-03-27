
import psycopg2

def test_rooms_db():
    try:
        conn = psycopg2.connect("postgresql://postgres:qwerty123@localhost:5432/orchiddb")
        cur = conn.cursor()
        cur.execute("SELECT id, number, status FROM rooms;")
        rooms = cur.fetchall()
        print("DB Rooms:", rooms)
        
        cur.execute("SELECT id, status, check_in, check_out FROM bookings WHERE status NOT IN ('cancelled', 'checked_out');")
        active_bookings = cur.fetchall()
        print("Active Bookings:", active_bookings)
        
        cur.execute("SELECT id, status, check_in, check_out FROM package_bookings WHERE status NOT IN ('cancelled', 'checked_out');")
        active_package_bookings = cur.fetchall()
        print("Active Package Bookings:", active_package_bookings)
        
        cur.execute("SELECT room_id, package_booking_id FROM package_booking_rooms;")
        pbr = cur.fetchall()
        print("Package Booking Rooms:", pbr)
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
        
if __name__ == "__main__":
    test_rooms_db()
