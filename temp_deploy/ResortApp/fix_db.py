import psycopg2

conn = psycopg2.connect('postgresql://postgres:qwerty123@localhost:5432/orchiddb')
cur = conn.cursor()

fixes = [
    # recipes table missing branch_id
    "ALTER TABLE recipes ADD COLUMN IF NOT EXISTS branch_id INTEGER REFERENCES branches(id) DEFAULT 1",
    # recipe_ingredients missing nothing visible yet, but check
    # stock reconciliations - table missing entirely, create it
    """CREATE TABLE IF NOT EXISTS stock_reconciliations (
        id SERIAL PRIMARY KEY,
        branch_id INTEGER REFERENCES branches(id),
        reconciliation_number VARCHAR,
        reconciliation_date TIMESTAMP DEFAULT NOW(),
        location_id INTEGER,
        status VARCHAR DEFAULT 'pending',
        notes TEXT,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    )""",
    "CREATE INDEX IF NOT EXISTS ix_stock_reconciliations_id ON stock_reconciliations(id)",
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
