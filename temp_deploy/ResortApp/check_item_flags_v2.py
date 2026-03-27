
import psycopg2

def check_item_flags():
    try:
        conn = psycopg2.connect("postgresql://postgres:qwerty123@localhost:5432/orchiddb")
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, is_sellable_to_guest, is_asset_fixed, track_laundry_cycle, is_perishable 
            FROM inventory_items 
            WHERE name ILIKE ANY(ARRAY['%chicken%', '%coca cola%', '%BED SHEET%', '%BATH TOWEL%', '%TV%', '%MILK%', '%MINERAL WATER%']);
        """)
        rows = cur.fetchall()
        print("ID | Name | Sellable | Fixed Asset | Laundry | Perishable")
        print("-" * 60)
        for row in rows:
            print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_item_flags()
