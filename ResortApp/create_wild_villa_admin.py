import psycopg2
from passlib.context import CryptContext
import json
import sys

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from app.database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        print("\nCreating branch 'Wild Villa'...")
        res = conn.execute(
            text("INSERT INTO branches (name, code, is_active, created_at) VALUES (:name, :code, :is_active, NOW()) RETURNING id"),
            {"name": "Wild Villa", "code": "WILDV", "is_active": True}
        )
        branch_id = res.fetchone()[0]
        print(f"  Branch created: ID {branch_id}")

        print("Creating superadmin role...")
        permissions = [
            "/dashboard", "/bookings", "/rooms", "/users", "/services",
            "/expenses", "/food", "/inventory", "/reports", "/settings",
            "/employees", "/finance", "/billing"
        ]
        res = conn.execute(
            text("INSERT INTO roles (name, permissions, branch_id) VALUES (:name, :permissions, :branch_id) RETURNING id"),
            {"name": "Superadmin", "permissions": json.dumps(permissions), "branch_id": branch_id}
        )
        role_id = res.fetchone()[0]
        print(f"  Role created: ID {role_id}")

        print("Creating superadmin user...")
        hashed_password = pwd_context.hash("admin123")
        res = conn.execute(
            text("""INSERT INTO users (name, email, hashed_password, phone, is_active, is_superadmin, role_id, branch_id)
               VALUES (:name, :email, :hashed_password, :phone, :is_active, :is_superadmin, :role_id, :branch_id) RETURNING id"""),
            {
                "name": "Super Admin", "email": "admin@orchid.com", "hashed_password": hashed_password,
                "phone": "0000000000", "is_active": True, "is_superadmin": True,
                "role_id": role_id, "branch_id": branch_id
            }
        )
        user_id = res.fetchone()[0]
        print(f"  User created: ID {user_id}")

        conn.commit()
    print("\n=== SUPERADMIN CREATED SUCCESSFULLY ===")
    print(f"  Email:    admin@orchid.com")
    print(f"  Password: admin123")
    print(f"  Branch:   Wild Villa (ID {branch_id})")
    print(f"  Role:     Superadmin (ID {role_id})")

except Exception as e:
    if 'conn' in locals():
        conn.rollback()
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close()
