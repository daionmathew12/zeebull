import psycopg2
conn = psycopg2.connect("postgresql://orchid_user:admin123@localhost/zeebulldb")
cur = conn.cursor()
tables = ["package_bookings", "checkouts", "expenses", "food_orders", "assigned_services", "packages"]
for table in tables:
    try:
        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'")
        cols = sorted([r[0] for r in cur.fetchall()])
        print(f"--- {table} ---")
        for c in cols:
            print(c)
    except Exception as e:
        print(f"ERROR:{table}:{e}")
cur.close()
conn.close()
