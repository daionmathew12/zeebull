import psycopg2

conn = psycopg2.connect("dbname=zeebulldb user=orchid_user password=admin123 host=localhost")
cur = conn.cursor()

cur.execute("SELECT id, name, code, is_active, created_at FROM branches")
print("Branches:", cur.fetchall())

cur.execute("SELECT id, name, email, branch_id, role_id, is_superadmin FROM users")
print("Users:", cur.fetchall())

cur.execute("SELECT id, name, branch_id FROM roles")
print("Roles:", cur.fetchall())

cur.close()
conn.close()
