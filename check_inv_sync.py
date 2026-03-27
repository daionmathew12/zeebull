
import psycopg2
from psycopg2.extras import RealDictCursor

def check_rooms_and_locations():
    try:
        conn = psycopg2.connect(
            dbname="zeebulldb",
            user="orchid_user",
            password="admin123",
            host="localhost",
            port="5432"
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check Rooms
        print("--- Rooms Check ---")
        cur.execute("SELECT id, number, branch_id, inventory_location_id, status FROM rooms")
        rooms = cur.fetchall()
        for r in rooms:
            print(f"Room {r['number']}: ID={r['id']}, Branch={r['branch_id']}, LocID={r['inventory_location_id']}, Status={r['status']}")
            
        # Check Locations of type GUEST_ROOM
        print("\n--- Locations (GUEST_ROOM) Check ---")
        cur.execute("SELECT id, name, branch_id, location_type, is_active, is_inventory_point FROM locations WHERE location_type = 'GUEST_ROOM'")
        locs = cur.fetchall()
        for l in locs:
            print(f"Location '{l['name']}': ID={l['id']}, Branch={l['branch_id']}, Type={l['location_type']}, Active={l['is_active']}, InvPoint={l['is_inventory_point']}")
            
        # Check for rooms without locations
        cur.execute("SELECT count(*) FROM rooms WHERE inventory_location_id IS NULL")
        unsynced = cur.fetchone()['count']
        print(f"\nUnsynced Rooms: {unsynced}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_rooms_and_locations()
