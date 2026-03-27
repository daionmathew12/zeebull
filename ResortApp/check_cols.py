import psycopg2

conn = psycopg2.connect('postgresql://postgres:qwerty123@localhost:5432/orchiddb')
cur = conn.cursor()

print("=== service_requests columns ===")
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='service_requests' ORDER BY column_name")
rows = cur.fetchall()
for r in rows:
    print(r[0])

print("\n=== stock_reconciliations columns ===")
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='stock_reconciliations' ORDER BY column_name")
rows = cur.fetchall()
for r in rows:
    print(r[0])

conn.close()
