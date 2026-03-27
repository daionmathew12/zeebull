#!/usr/bin/env python3
"""
Get roles table schema
"""
import psycopg2
conn = psycopg2.connect(host="localhost", port=5432, dbname="zeebulldb", user="orchid_user", password="admin123")
cur = conn.cursor()
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='roles' ORDER BY ordinal_position")
print("roles columns:")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")
cur.close()
conn.close()
