#!/usr/bin/env python3
import psycopg2

conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="zeebulldb", user="orchid_user", password="admin123"
)
cur = conn.cursor()

tables = ["users", "bookings", "rooms", "food_items", "services", "employees"]
print("\n=== DB Row Counts After Clear ===")
for t in tables:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        count = cur.fetchone()[0]
        status = "✓ EMPTY" if count == 0 else f"⚠ HAS {count} ROWS"
        print(f"  {t}: {count} rows  {status}")
    except Exception as e:
        print(f"  {t}: ERROR - {e}")

cur.execute("SELECT id, email, is_superadmin FROM users")
users = cur.fetchall()
print(f"\nUsers remaining: {users}")
print("\n=== Done ===")
cur.close()
conn.close()
