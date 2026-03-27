import psycopg2
from datetime import datetime

conn = psycopg2.connect("dbname=zeebulldb user=orchid_user password=admin123 host=localhost")
cur = conn.cursor()

try:
    # Fix the branch row - set is_active and created_at which were left NULL
    cur.execute("""
        UPDATE branches 
        SET is_active = TRUE, created_at = %s 
        WHERE is_active IS NULL OR created_at IS NULL
    """, (datetime.utcnow(),))
    print(f"Updated {cur.rowcount} branch rows")
    
    # Verify
    cur.execute("SELECT id, name, code, is_active, created_at FROM branches")
    for row in cur.fetchall():
        print(f"  Branch: {row}")
    
    conn.commit()
    print("Done.")

except Exception as e:
    conn.rollback()
    print(f"ERROR: {e}")
finally:
    cur.close()
    conn.close()
