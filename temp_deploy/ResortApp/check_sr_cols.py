import psycopg2
try:
    conn = psycopg2.connect('postgresql://postgres:qwerty123@localhost:5432/orchiddb')
    cur = conn.cursor()
    
    # Check tables
    for table in ['service_requests', 'assigned_services']:
        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}'")
        cols = [r[0] for r in cur.fetchall()]
        print(f"Table {table}: {cols}")
        
        if 'billing_status' not in cols:
            print(f"Adding billing_status to {table}")
            cur.execute(f"ALTER TABLE {table} ADD COLUMN billing_status VARCHAR DEFAULT 'unbilled'")
            conn.commit()
            
    conn.close()
    print("Check complete")
except Exception as e:
    print(f"Error: {e}")
