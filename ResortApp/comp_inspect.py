import psycopg2

def check_table(cur, table):
    try:
        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}'")
        cols = sorted([r[0] for r in cur.fetchall()])
        print(f"Table {table} columns ({len(cols)}):")
        for c in cols:
            print(f"  - {c}")
    except Exception as e:
        print(f"Error checking {table}: {e}")

try:
    conn = psycopg2.connect('postgresql://postgres:qwerty123@localhost:5432/orchiddb')
    cur = conn.cursor()
    
    check_table(cur, 'food_categories')
    check_table(cur, 'food_items')
    check_table(cur, 'food_orders')
    check_table(cur, 'food_order_items')
    check_table(cur, 'inventory_categories')
    check_table(cur, 'inventory_items')
    check_table(cur, 'service_requests')
    check_table(cur, 'assigned_services')
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
