import psycopg2
from passlib.context import CryptContext
import json

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

conn = psycopg2.connect("dbname=zeebulldb user=orchid_user password=admin123 host=localhost")
cur = conn.cursor()

try:
    # Get branches table columns
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='branches' ORDER BY ordinal_position")
    branch_cols = [r[0] for r in cur.fetchall()]
    print("Branch columns:", branch_cols)

    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='roles' ORDER BY ordinal_position")
    role_cols = [r[0] for r in cur.fetchall()]
    print("Role columns:", role_cols)

    print("\nCreating branch...")
    cur.execute("INSERT INTO branches (name, code) VALUES (%s, %s) RETURNING id", ("Main Branch", "MAIN"))
    branch_id = cur.fetchone()[0]
    print(f"  Branch created: ID {branch_id}")

    print("Creating superadmin role...")
    permissions = [
        "/dashboard", "/bookings", "/rooms", "/users", "/services",
        "/expenses", "/food", "/inventory", "/reports", "/settings",
        "/employees", "/finance", "/billing"
    ]
    cur.execute(
        "INSERT INTO roles (name, permissions, branch_id) VALUES (%s, %s, %s) RETURNING id",
        ("Superadmin", json.dumps(permissions), branch_id)
    )
    role_id = cur.fetchone()[0]
    print(f"  Role created: ID {role_id}")

    print("Creating superadmin user...")
    hashed_password = pwd_context.hash("admin123")
    cur.execute(
        """INSERT INTO users (name, email, hashed_password, phone, is_active, is_superadmin, role_id, branch_id)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
        ("Super Admin", "admin@orchid.com", hashed_password, "0000000000", True, True, role_id, branch_id)
    )
    user_id = cur.fetchone()[0]
    print(f"  User created: ID {user_id}")

    conn.commit()
    print("\n=== SUPERADMIN CREATED SUCCESSFULLY ===")
    print(f"  Email:    admin@orchid.com")
    print(f"  Password: admin123")
    print(f"  Branch:   Main Branch (ID {branch_id})")
    print(f"  Role:     Superadmin (ID {role_id})")

except Exception as e:
    conn.rollback()
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
