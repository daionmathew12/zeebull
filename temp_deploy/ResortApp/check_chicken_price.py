
import psycopg2
from tabulate import tabulate

def check_item_price():
    try:
        conn = psycopg2.connect("postgresql://postgres:qwerty123@localhost:5432/orchiddb")
        cur = conn.cursor()
        
        # Check the item details
        cur.execute("SELECT id, name, unit_price, selling_price, category_id FROM inventory_items WHERE name ILIKE '%chicken%' OR id = 15;")
        rows = cur.fetchall()
        headers = [desc[0] for desc in cur.description]
        print("--- Inventory Item Details ---")
        print(tabulate(rows, headers=headers))
        
        # Also check if it's currently assigned to a room with a specific price
        cur.execute("SELECT * FROM room_inventory_items WHERE inventory_item_id = 15 LIMIT 5;")
        rows = cur.fetchall()
        if rows:
            headers = [desc[0] for desc in cur.description]
            print("\n--- Room Inventory Assignment Details ---")
            print(tabulate(rows, headers=headers))
        else:
            print("\nNo specific room inventory assignments found in room_inventory_items table.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_item_price()
