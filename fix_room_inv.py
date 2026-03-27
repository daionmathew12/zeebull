
import psycopg2
from psycopg2.extras import RealDictCursor

def fix_room_inventory_links():
    try:
        conn = psycopg2.connect(
            dbname="zeebulldb",
            user="orchid_user",
            password="admin123",
            host="localhost",
            port="5432"
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print("Resetting all room inventory location links...")
        cur.execute("UPDATE rooms SET inventory_location_id = NULL")
        print(f"✓ {cur.rowcount} rooms updated.")
        
        print("Cleaning up GUEST_ROOM locations to ensure re-sync works fresh...")
        # We delete them so they get re-created with correct branch_id and data
        cur.execute("DELETE FROM locations WHERE location_type = 'GUEST_ROOM'")
        print(f"✓ {cur.rowcount} GUEST_ROOM locations deleted.")
        
        conn.commit()
        cur.close()
        conn.close()
        print("\nFix completed successfully. Next time you visit the inventory locations tab, rooms will be correctly synced for your branch.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_room_inventory_links()
