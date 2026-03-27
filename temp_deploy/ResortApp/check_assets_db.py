
import psycopg2

def check_assets():
    try:
        conn = psycopg2.connect("postgresql://postgres:qwerty123@localhost:5432/orchiddb")
        cur = conn.cursor()
        
        print("--- Asset Mappings ---")
        cur.execute("SELECT * FROM asset_mappings;")
        rows = cur.fetchall()
        for row in rows:
            print(row)
            
        print("\n--- Asset Registry ---")
        cur.execute("SELECT * FROM asset_registry;")
        rows = cur.fetchall()
        for row in rows:
            print(row)
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_assets()
