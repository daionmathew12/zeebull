
import psycopg2

def check_loc_16():
    try:
        conn = psycopg2.connect("postgresql://postgres:qwerty123@localhost:5432/orchiddb")
        cur = conn.cursor()
        
        cur.execute("SELECT name FROM locations WHERE id = 16;")
        row = cur.fetchone()
        print(f"Location 16 Name: {row[0] if row else 'None'}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_loc_16()
