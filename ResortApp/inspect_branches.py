import psycopg2
try:
    conn = psycopg2.connect('postgresql://postgres:qwerty123@localhost:5432/orchiddb')
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_name='branches'")
    print(f"Table branches exists: {bool(cur.fetchone())}")
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='branches'")
    print(f"Columns: {[r[0] for r in cur.fetchall()]}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
