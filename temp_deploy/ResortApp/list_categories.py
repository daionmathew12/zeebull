
import psycopg2

def list_cats():
    conn = psycopg2.connect("postgresql://postgres:qwerty123@localhost:5432/orchiddb")
    cur = conn.cursor()
    cur.execute("SELECT name FROM inventory_categories;")
    rows = cur.fetchall()
    for row in rows:
        print(row[0])
    cur.close()
    conn.close()

if __name__ == "__main__":
    list_cats()
