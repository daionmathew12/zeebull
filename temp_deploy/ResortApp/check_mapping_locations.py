
import psycopg2

def check_mapping_locations():
    try:
        conn = psycopg2.connect("postgresql://postgres:qwerty123@localhost:5432/orchiddb")
        cur = conn.cursor()
        
        cur.execute("""
            SELECT am.id, i.name, l.name, l.is_inventory_point, l.location_type 
            FROM asset_mappings am
            JOIN inventory_items i ON am.item_id = i.id
            JOIN locations l ON am.location_id = l.id;
        """)
        rows = cur.fetchall()
        print("Mapping ID | Item | Location | is_inv_point | type")
        print("-" * 70)
        for row in rows:
            print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_mapping_locations()
