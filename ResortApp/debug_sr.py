import psycopg2

conn = psycopg2.connect('postgresql://postgres:qwerty123@localhost:5432/orchiddb')
cur = conn.cursor()

# Test the service-requests query to find the error
try:
    cur.execute("SELECT * FROM service_requests LIMIT 1")
    cols = [d[0] for d in cur.description]
    print("service_requests columns:", cols)
except Exception as e:
    print("ERROR service_requests:", e)
    conn.rollback()

# Check what's in employees table
try:
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='employees' ORDER BY column_name")
    print("\nemployees columns:", [r[0] for r in cur.fetchall()])
except Exception as e:
    print("ERROR employees:", e)
    conn.rollback()

# Check services table
try:
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='services' ORDER BY column_name")
    print("\nservices columns:", [r[0] for r in cur.fetchall()])
except Exception as e:
    print("ERROR services:", e)
    conn.rollback()

# Check assigned_services table
try:
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='assigned_services' ORDER BY column_name")
    print("\nassigned_services columns:", [r[0] for r in cur.fetchall()])
except Exception as e:
    print("ERROR assigned_services:", e)
    conn.rollback()

conn.close()
