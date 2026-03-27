import psycopg2
conn = psycopg2.connect("postgresql://postgres:qwerty123@localhost:5432/orchiddb")
cur = conn.cursor()
cur.execute("SELECT * FROM branches;")
cols = [desc[0] for desc in cur.description]
rows = cur.fetchall()
for row in rows:
    print(dict(zip(cols, row)))
cur.close()
conn.close()
