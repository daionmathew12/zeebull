import psycopg2
from passlib.context import CryptContext
import json

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

conn = psycopg2.connect("dbname=zeebulldb user=orchid_user password=admin123 host=localhost")
cur = conn.cursor()

try:
    # Get user table columns
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users' ORDER BY ordinal_position")
    cols = [r[0] for r in cur.fetchall()]
    print("User table columns:", cols)
    
    # Get branches
    cur.execute("SELECT id, name FROM branches")
    branches = cur.fetchall()
    print("Branches:", branches)

    # Get roles
    cur.execute("SELECT id, name FROM roles LIMIT 10")
    roles = cur.fetchall()
    print("Roles:", roles)

    # Get current users
    cur.execute("SELECT id, email, name FROM users")
    users = cur.fetchall()
    print("Current users:", users)

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
