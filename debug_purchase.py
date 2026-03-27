import psycopg2
conn = psycopg2.connect("postgresql://postgres:qwerty123@localhost:5432/orchiddb")
cur = conn.cursor()
cur.execute("SELECT id, purchase_number, branch_id, status FROM purchase_masters WHERE purchase_number = 'PO-20260312-0001';")
print(cur.fetchone())
cur.execute("SELECT id, name FROM branches;")
print(cur.fetchall())
cur.close()
conn.close()
