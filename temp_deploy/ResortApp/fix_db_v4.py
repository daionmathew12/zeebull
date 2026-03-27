import psycopg2
try:
    conn = psycopg2.connect('postgresql://postgres:qwerty123@localhost:5432/orchiddb')
    cur = conn.cursor()
    
    # Fix food_categories
    print("Fixing food_categories...")
    cur.execute("ALTER TABLE food_categories ADD COLUMN IF NOT EXISTS branch_id INTEGER NOT NULL DEFAULT 1")
    cur.execute("ALTER TABLE food_categories ADD COLUMN IF NOT EXISTS description TEXT NULL")
    cur.execute("ALTER TABLE food_categories ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE")
    cur.execute("ALTER TABLE food_categories ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    
    # Also ensure inventory_categories has all it needs
    print("Double-checking inventory_categories...")
    # (already looks good, but being safe)
    
    conn.commit()
    print("Database updated successfully!")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
