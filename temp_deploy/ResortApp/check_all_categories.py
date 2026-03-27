
import psycopg2

def check_all_categories():
    try:
        conn = psycopg2.connect("postgresql://postgres:qwerty123@localhost:5432/orchiddb")
        cur = conn.cursor()
        
        cur.execute("SELECT id, name, is_asset_fixed FROM inventory_categories;")
        rows = cur.fetchall()
        print("ID | Name | is_asset_fixed")
        print("-" * 30)
        for row in rows:
            print(f"{row[0]} | {row[1]} | {row[2]}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_all_categories()
