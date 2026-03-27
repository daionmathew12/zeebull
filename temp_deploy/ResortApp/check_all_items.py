
import psycopg2

def check_item_flags():
    conn = psycopg2.connect("postgresql://postgres:qwerty123@localhost:5432/orchiddb")
    cur = conn.cursor()
    cur.execute("SELECT id, name, is_asset_fixed FROM inventory_items;")
    rows = cur.fetchall()
    for row in rows:
        print(row)
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_item_flags()
