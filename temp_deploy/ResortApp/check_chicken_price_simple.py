
import psycopg2

def check_item_price():
    try:
        conn = psycopg2.connect("postgresql://postgres:qwerty123@localhost:5432/orchiddb")
        cur = conn.cursor()
        
        # Check the item details
        cur.execute("SELECT id, name, unit_price, selling_price, category_id FROM inventory_items WHERE name ILIKE '%chicken%' OR id = 15;")
        rows = cur.fetchall()
        print("--- Inventory Item Details ---")
        for row in rows:
            print(row)
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_item_price()
