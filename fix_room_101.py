
import psycopg2

def fix_room_101():
    conn = psycopg2.connect("host=localhost port=5432 user=postgres dbname=orchiddb")
    cur = conn.cursor()
    
    print("Clearing package booking #1 for Room 101...")
    cur.execute("UPDATE package_bookings SET status = 'cancelled' WHERE id = 1;")
    
    print("Resetting Room 101 status...")
    cur.execute("UPDATE rooms SET status = 'Available' WHERE number = '101';")
    
    conn.commit()
    print("Success!")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    fix_room_101()
