import psycopg2
try:
    conn = psycopg2.connect('postgresql://postgres:qwerty123@localhost:5432/orchiddb')
    cur = conn.cursor()
    
    tables = ['food_items', 'food_categories', 'food_orders', 'food_order_items']
    for table in tables:
        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}'")
        cols = [r[0] for r in cur.fetchall()]
        print(f"Table {table}: {cols}")
            
    conn.close()
except Exception as e:
    print(f"Error: {e}")
