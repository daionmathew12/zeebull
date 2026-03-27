
import psycopg2

def check_item_cat():
    conn = psycopg2.connect("postgresql://postgres:qwerty123@localhost:5432/orchiddb")
    cur = conn.cursor()
    cur.execute("SELECT i.name, c.name as category_name FROM inventory_items i JOIN inventory_categories c ON i.category_id = c.id WHERE i.id IN (15, 18);")
    rows = cur.fetchall()
    for row in rows:
        print(row)
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_item_cat()
