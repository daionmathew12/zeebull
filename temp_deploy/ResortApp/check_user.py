import psycopg2
conn = psycopg2.connect('postgresql://postgres:qwerty123@localhost:5432/orchiddb', connect_timeout=5)
cur = conn.cursor()
cur.execute("SELECT u.email, u.is_active, r.name FROM users u JOIN roles r ON u.role_id = r.id WHERE u.email='admin@orchid.com'")
print(cur.fetchone())
conn.close()
