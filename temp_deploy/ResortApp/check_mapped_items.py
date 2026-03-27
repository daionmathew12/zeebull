
import psycopg2

def check_mapped_items():
    try:
        conn = psycopg2.connect("postgresql://postgres:qwerty123@localhost:5432/orchiddb")
        cur = conn.cursor()
        
        cur.execute("""
            SELECT DISTINCT i.id, i.name, i.is_asset_fixed 
            FROM asset_mappings am
            JOIN inventory_items i ON am.item_id = i.id;
        """)
        rows = cur.fetchall()
        print("Mapped Item ID | Name | is_asset_fixed")
        print("-" * 50)
        for row in rows:
            print(f"{row[0]} | {row[1]} | {row[2]}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_mapped_items()
