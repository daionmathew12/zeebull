import psycopg2
conn = psycopg2.connect("postgresql://postgres:qwerty123@localhost:5432/orchiddb")
cur = conn.cursor()
cur.execute("SELECT id, name FROM branches WHERE name ILIKE '%Zeebul%';")
print(cur.fetchall())
cur.close()
conn.close()
