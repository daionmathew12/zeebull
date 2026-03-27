import psycopg2
conn = psycopg2.connect("postgresql://orchid_user:admin123@localhost/zeebulldb")
cur = conn.cursor()
cur.execute("SELECT action, status_code, timestamp FROM activity_logs ORDER BY timestamp DESC LIMIT 20")
for r in cur.fetchall():
    print(r)
cur.close()
conn.close()
