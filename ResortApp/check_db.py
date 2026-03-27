import psycopg2
conn = psycopg2.connect('postgresql://postgres:qwerty123@localhost:5432/orchiddb', connect_timeout=5)
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM inventory_items")
print("inventory_items:", cur.fetchone())

cur.execute("SELECT COUNT(*) FROM inventory_categories")
print("inventory_categories:", cur.fetchone())

cur.execute("SELECT COUNT(*) FROM vendors")
print("vendors:", cur.fetchone())

cur.execute("SELECT COUNT(*) FROM branches")
print("branches:", cur.fetchone())

cur.execute("SELECT id, name FROM branches LIMIT 10")
rows = cur.fetchall()
print("branches list:", rows)

cur.execute("SELECT id, name, branch_id FROM inventory_items LIMIT 5")
rows = cur.fetchall()
print("sample items:", rows)

cur.execute("SELECT id, name, branch_id FROM inventory_categories LIMIT 5")
rows = cur.fetchall()
print("sample categories:", rows)

conn.close()
print("DONE")
