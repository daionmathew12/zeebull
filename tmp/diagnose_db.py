import os
import sys

# Add the project root to sys.path
sys.path.append('/var/www/zeebull/ResortApp')

from app.database import SessionLocal
from sqlalchemy import text

def diagnose():
    db = SessionLocal()
    try:
        print("--- DB DIAGNOSTICS ---")
        
        # 1. Check Branches
        branches = db.execute(text("SELECT id, name FROM branches")).fetchall()
        print(f"Branches found ({len(branches)}):")
        for b in branches:
            print(f" - {b.id}: {b.name}")
            
        # 2. Check Roles
        roles = db.execute(text("SELECT id, name FROM roles")).fetchall()
        print(f"\nRoles found ({len(roles)}):")
        for r in roles:
            print(f" - {r.id}: {r.name}")
            
        # 3. Check Admin User
        admin = db.execute(text("SELECT id, email, is_active, role_id, branch_id FROM users WHERE email='admin@orchid.com'")).fetchone()
        print(f"\nAdmin account check (admin@orchid.com):")
        if admin:
            print(f" - ID: {admin.id}")
            print(f" - Email: {admin.email}")
            print(f" - Active: {admin.is_active}")
            print(f" - Role ID: {admin.role_id}")
            print(f" - Branch ID: {admin.branch_id}")
            
            # Check role name
            if admin.role_id:
                role_name = db.execute(text(f"SELECT name FROM roles WHERE id={admin.role_id}")).scalar()
                print(f" - Role Name: {role_name}")
        else:
            print(" - ERROR: Admin user NOT FOUND!")

        # 4. Check Employees associated with Admin
        if admin:
            emp = db.execute(text(f"SELECT id, name FROM employees WHERE user_id={admin.id}")).fetchone()
            print(f"\nEmployee associated with admin:")
            if emp:
                print(f" - {emp.id}: {emp.name}")
            else:
                print(" - None")

    except Exception as e:
        print(f"\nDIAGNOSTICS FAILED: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    diagnose()
