import psycopg2
from passlib.hash import bcrypt
from datetime import timezone, datetime
import json

def create_superadmin():
    try:
        # Connection for new VM
        conn = psycopg2.connect(
            dbname="zeebulldb",
            user="zeebull",
            password="zeebullpass",
            host="localhost"
        )
        cur = conn.cursor()

        print("Checking for existing branch...")
        cur.execute("SELECT id FROM branches LIMIT 1")
        branch_id = cur.fetchone()
        
        if not branch_id:
            print("Creating branch...")
            cur.execute(
                "INSERT INTO branches (name, code, is_active, created_at) VALUES (%s, %s, %s, %s) RETURNING id",
                ("Main Branch", "MAIN", True, datetime.now(timezone.utc))
            )
            branch_id = cur.fetchone()[0]
            print(f"  Branch created: ID {branch_id}")
        else:
            branch_id = branch_id[0]
            print(f"  Using existing branch: ID {branch_id}")

        print("Creating superadmin role...")
        permissions = [
            "all", "admin", "dashboard", "room_management", "booking_management",
            "payment_management", "report_access", "settings_management"
        ]
        cur.execute(
            "INSERT INTO roles (name, permissions, branch_id) VALUES (%s, %s, %s) RETURNING id",
            ("Superadmin", json.dumps(permissions), branch_id)
        )
        role_id = cur.fetchone()[0]
        print(f"  Role created: ID {role_id}")

        print("Creating superadmin user...")
        hashed_password = bcrypt.hash("admin123")
        cur.execute(
            """INSERT INTO users 
               (name, email, hashed_password, role_id, branch_id, is_superadmin, is_active) 
               VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            ("Super Admin", "admin@orchid.com", hashed_password, role_id, branch_id, True, True)
        )
        user_id = cur.fetchone()[0]
        print(f"  User created: ID {user_id}")

        conn.commit()
        print("\n=== SUPERADMIN CREATED SUCCESSFULLY ===")
        print(f"  Email:    admin@orchid.com")
        print(f"  Password: admin123")
        
        cur.close()
        conn.close()

    except Exception as e:
        print(f"ERROR: {e}")
        if 'conn' in locals():
            conn.rollback()

if __name__ == "__main__":
    create_superadmin()
