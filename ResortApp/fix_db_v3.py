import psycopg2

conn = psycopg2.connect('postgresql://postgres:qwerty123@localhost:5432/orchiddb')
cur = conn.cursor()

# Ensure all missing columns across key tables are fixed
fixes = [
    "ALTER TABLE service_requests ADD COLUMN IF NOT EXISTS billing_status VARCHAR DEFAULT 'unbilled'",
    "ALTER TABLE assigned_services ADD COLUMN IF NOT EXISTS billing_status VARCHAR DEFAULT 'unbilled'",
    "ALTER TABLE service_requests ADD COLUMN IF NOT EXISTS started_at TIMESTAMP NULL",
    "ALTER TABLE service_requests ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP NULL",
    "ALTER TABLE service_requests ADD COLUMN IF NOT EXISTS pickup_location_id INTEGER REFERENCES locations(id) NULL",
    "ALTER TABLE assigned_services ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMP NULL",
    "ALTER TABLE assigned_services ADD COLUMN IF NOT EXISTS started_at TIMESTAMP NULL",
    "ALTER TABLE assigned_services ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP NULL",
    "ALTER TABLE assigned_services ADD COLUMN IF NOT EXISTS override_charges FLOAT NULL",
    "ALTER TABLE inventory_categories ADD COLUMN IF NOT EXISTS parent_department VARCHAR NULL"
]

for sql in fixes:
    try:
        cur.execute(sql)
        print(f"OK: {sql[:60]}...")
        conn.commit()
    except Exception as e:
        print(f"SKIP ({e})")
        conn.rollback()

conn.close()
print("Done")
