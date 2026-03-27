import psycopg2
try:
    conn = psycopg2.connect('postgresql://postgres:qwerty123@localhost:5432/orchiddb')
    cur = conn.cursor()
    
    cur.execute("SELECT table_name, column_name FROM information_schema.columns WHERE column_name='parent_department'")
    print(f"Column parent_department found in: {cur.fetchall()}")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
