#!/usr/bin/env python3
"""
Clear ALL data in zeebulldb using pure SQL/psycopg2. No ORM dependency.
Keeps only the superadmin user.
"""
import psycopg2
from psycopg2.extras import execute_values
from passlib.context import CryptContext

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="zeebulldb",
    user="orchid_user",
    password="admin123"
)
conn.autocommit = False
cur = conn.cursor()

try:
    print("Fetching all table names...")
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
    tables = [r[0] for r in cur.fetchall()]
    print(f"Tables: {tables}")

    print("\nTruncating all tables with CASCADE...")
    # Truncate everything at once in one command
    table_list = ", ".join(tables)
    cur.execute(f"TRUNCATE TABLE {table_list} RESTART IDENTITY CASCADE")
    conn.commit()
    print("✓ All tables cleared!")

    # Re-seed roles
    print("\nSeeding roles...")
    admin_permissions = '["/dashboard","/bookings","/rooms","/users","/services","/expenses","/food-orders","/food-categories","/food-items","/billing","/account","/Userfrontend_data","/packages","/report","/guestprofiles","/user-history","/employee-management","/employee-dashboard","/inventory","/settings","/branch-management","/activity-logs","/laundry"]'
    cur.execute(
        "INSERT INTO roles (name, permissions, branch_id) VALUES (%s, %s, %s) RETURNING id",
        ('admin', admin_permissions, None)
    )
    admin_role_id = cur.fetchone()[0]

    for role_name in ['housekeeping', 'kitchen', 'waiter', 'maintenance']:
        cur.execute(
            "INSERT INTO roles (name, permissions, branch_id) VALUES (%s, %s, %s)",
            (role_name, '["/employee-dashboard"]', None)
        )
    conn.commit()
    print(f"✓ Roles seeded. Admin role ID: {admin_role_id}")

    # Re-seed superadmin
    print("\nSeeding superadmin user...")
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed = pwd_context.hash("admin123")

    cur.execute("""
        INSERT INTO users (email, hashed_password, name, is_active, is_superadmin, role_id, branch_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, ("admin@orchid.com", hashed, "Super Admin", True, True, admin_role_id, None))
    conn.commit()
    print("✓ Superadmin created: admin@orchid.com / admin123")

    # Verify
    cur.execute("SELECT id, email, is_superadmin FROM users")
    users = cur.fetchall()
    print(f"\nUsers in DB: {users}")
    print("\n✅ Database clear complete! All data removed, superadmin retained.")

except Exception as e:
    conn.rollback()
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
