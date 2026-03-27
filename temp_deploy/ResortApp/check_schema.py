import psycopg2

conn = psycopg2.connect('postgresql://postgres:qwerty123@localhost:5432/orchiddb')
cur = conn.cursor()

# Check what tables exist related to the 500 errors we see
print("=== Tables with 'audit' in name ===")
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name ILIKE '%audit%'")
for r in cur.fetchall():
    print(r[0])

print("\n=== food_categories columns ===")
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='food_categories' ORDER BY column_name")
for r in cur.fetchall():
    print(r[0])

print("\n=== recipes columns ===")
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='recipes' ORDER BY column_name")
for r in cur.fetchall():
    print(r[0])

print("\n=== inventory_categories columns ===")
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='inventory_categories' ORDER BY column_name")
for r in cur.fetchall():
    print(r[0])

conn.close()
