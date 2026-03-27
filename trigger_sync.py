
import psycopg2
from psycopg2.extras import RealDictCursor
import sys

def sync_and_check(branch_id):
    try:
        conn = psycopg2.connect(
            dbname="zeebulldb",
            user="orchid_user",
            password="admin123",
            host="localhost",
            port="5432"
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print(f"--- Syncing Rooms for Branch {branch_id} ---")
        # Find unsynced rooms for this branch
        cur.execute("SELECT id, number FROM rooms WHERE inventory_location_id IS NULL AND branch_id = %s", (branch_id,))
        rooms = cur.fetchall()
        
        for room in rooms:
            # Check if location exists
            cur.execute("""
                SELECT id FROM locations 
                WHERE (name = %s OR room_area = %s) 
                AND location_type = 'GUEST_ROOM' 
                AND branch_id = %s
            """, (f"Room {room['number']}", f"Room {room['number']}", branch_id))
            loc = cur.fetchone()
            
            if not loc:
                print(f"Creating location for Room {room['number']}...")
                cur.execute("""
                    INSERT INTO locations (name, building, room_area, location_type, is_inventory_point, is_active, branch_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (f"Room {room['number']}", "Main Building", f"Room {room['number']}", "GUEST_ROOM", False, True, branch_id))
                loc_id = cur.fetchone()['id']
            else:
                loc_id = loc['id']
                print(f"Found existing location {loc_id} for Room {room['number']}.")
                
            cur.execute("UPDATE rooms SET inventory_location_id = %s WHERE id = %s", (loc_id, room['id']))
            
        conn.commit()
        print(f"✓ Sync completed for Branch {branch_id}.")
        
        # Check Final State
        print("\n--- Final State Check ---")
        cur.execute("SELECT id, number, branch_id, inventory_location_id FROM rooms ORDER BY branch_id, number")
        results = cur.fetchall()
        for r in results:
            print(f"Room {r['number']}: ID={r['id']}, Branch={r['branch_id']}, LocID={r['inventory_location_id']}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        sync_and_check(int(sys.argv[1]))
    else:
        sync_and_check(1)
        sync_and_check(2)
