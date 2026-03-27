import psycopg2
try:
    conn = psycopg2.connect('postgresql://postgres:qwerty123@localhost:5432/orchiddb')
    cur = conn.cursor()
    
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='service_inventory_items'")
    print(f"Table service_inventory_items: {cur.fetchall()}")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
