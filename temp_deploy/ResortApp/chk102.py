
import psycopg2

def check_room_102_assets():
    try:
        conn = psycopg2.connect("postgresql://postgres:qwerty123@localhost:5432/orchiddb")
        cur = conn.cursor()
        
        cur.execute("""
            SELECT i.id, i.name, i.is_asset_fixed 
            FROM asset_mappings am
            JOIN inventory_items i ON am.item_id = i.id
            JOIN locations l ON am.location_id = l.id
            WHERE l.name = 'Room 102';
        """)
        rows = cur.fetchall()
        print("Item ID | Name | is_asset_fixed")
        print("-" * 30)
        for row in rows:
            print(f"{row[0]} | {row[1]} | {row[2]}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_room_102_assets()
