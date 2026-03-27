
import psycopg2
import json

def debug_room_101():
    conn = psycopg2.connect("host=localhost port=5432 user=postgres dbname=orchiddb")
    cur = conn.cursor()
    
    print("--- Room 101 Status ---")
    cur.execute("SELECT id, number, status, branch_id FROM rooms WHERE number = '101';")
    room = cur.fetchone()
    print(f"Room: {room}")
    
    if not room:
        print("Room 101 not found!")
        return
    
    room_id = room[0]
    branch_id = room[3]
    
    print("\n--- Regular Bookings for Room 101 ---")
    cur.execute("""
        SELECT b.id, b.display_id, b.status, b.check_in, b.check_out, b.guest_name
        FROM bookings b
        JOIN booking_rooms br ON b.id = br.booking_id
        WHERE br.room_id = %s;
    """, (room_id,))
    bookings = cur.fetchall()
    for b in bookings:
        print(b)
        
    print("\n--- Package Bookings for Room 101 ---")
    cur.execute("""
        SELECT pb.id, pb.status, pb.check_in, pb.check_out, pb.guest_name
        FROM package_bookings pb
        JOIN package_booking_rooms pbr ON pb.id = pbr.package_booking_id
        WHERE pbr.room_id = %s;
    """, (room_id,))
    pbookings = cur.fetchall()
    for pb in pbookings:
        print(pb)
        
    cur.close()
    conn.close()

if __name__ == "__main__":
    debug_room_101()
