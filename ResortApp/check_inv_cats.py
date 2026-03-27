import psycopg2
try:
    conn = psycopg2.connect('postgresql://postgres:qwerty123@localhost:5432/orchiddb')
    cur = conn.cursor()
    cur.execute("SELECT id, name, parent_department FROM inventory_categories")
    rows = cur.fetchall()
    print("Inventory Categories:")
    for row in rows:
        print(row)
    conn.close()
except Exception as e:
    print(f"Error: {e}")
