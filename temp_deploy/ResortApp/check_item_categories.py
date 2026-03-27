
import psycopg2

def check_item_categories():
    try:
        conn = psycopg2.connect("postgresql://postgres:qwerty123@localhost:5432/orchiddb")
        cur = conn.cursor()
        
        cur.execute("""
            SELECT i.name, c.name, c.is_asset_fixed 
            FROM inventory_items i 
            JOIN inventory_categories c ON i.category_id = c.id 
            WHERE i.id IN (12, 22);
        """)
        rows = cur.fetchall()
        print("Item Name | Category Name | Category is_asset_fixed")
        print("-" * 50)
        for row in rows:
            print(f"{row[0]} | {row[1]} | {row[2]}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_item_categories()
