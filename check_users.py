import psycopg2
conn = psycopg2.connect("postgresql://postgres:qwerty123@localhost:5432/orchiddb")
cur = conn.cursor()
cur.execute("SELECT id, name, email, branch_id, is_superadmin FROM users WHERE is_superadmin = True;")
cols = [desc[0] for desc in cur.description]
rows = cur.fetchall()
for row in rows:
    print(dict(zip(cols, row)))
cur.close()
conn.close()
