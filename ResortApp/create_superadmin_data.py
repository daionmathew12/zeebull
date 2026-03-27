import sys
import os
import json

# Add current directory to path so we can import app modules
sys.path.append(os.getcwd())

from app.database import SessionLocal, engine
from app.models.user import User, Role
from app.models.branch import Branch
from app.utils.auth import get_password_hash

def create_initial_data():
    db = SessionLocal()
    try:
        # 1. Create Branch "orchid trails"
        # 1. Create OR USE Branch 
        branch = db.query(Branch).first()
        if not branch:
            branch_name = "orchid trails"
            branch_code = "TRAILS"
            print(f"Creating branch '{branch_name}'...")
            branch = Branch(
                name=branch_name,
                code=branch_code,
                is_active=True
            )
            db.add(branch)
            db.commit()
            db.refresh(branch)
            print(f"Branch created with ID: {branch.id}")
        else:
            print(f"Using existing branch ID: {branch.id} ('{branch.name}')")
            # Optional: Rename it to 'orchid trails' if it's generic
            if branch.name == "Main Branch":
                 branch.name = "orchid trails"
                 branch.code = "TRAILS"
                 db.commit()
                 print("Renamed existing 'Main Branch' to 'orchid trails'")

        # 2. Create 'superadmin' role
        role_name = "superadmin"
        # Grant all major dashboard/system permissions
        perms = [
            "/dashboard", "/superadmin-dashboard", "/branches", "/bookings", "/rooms", 
            "/services", "/expenses", "/food-orders", "/billing", "/packages", 
            "/users", "/roles", "/employees", "/reports", "/inventory", "/setup"
        ]
        role = db.query(Role).filter(Role.name == role_name, Role.branch_id == branch.id).first()
        if not role:
            print(f"Creating role '{role_name}'...")
            role = Role(
                name=role_name,
                permissions=json.dumps(perms),
                branch_id=branch.id
            )
            db.add(role)
            db.commit()
            db.refresh(role)
            print(f"Role created with ID: {role.id}")
        else:
            print(f"Role '{role_name}' already exists.")

        # 3. Create Super Admin User
        email = "superadmin@orchid.com"
        password = "admin123"
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"Creating user '{email}'...")
            user = User(
                name="Orchid SuperAdmin",
                email=email,
                hashed_password=get_password_hash(password),
                role_id=role.id,
                branch_id=branch.id,
                is_active=True,
                is_superadmin=True
            )
            db.add(user)
            db.commit()
            print("Super Admin user created successfully.")
        else:
            print(f"User '{email}' already exists. Updating role and superadmin status...")
            user.role_id = role.id
            user.branch_id = branch.id
            user.is_superadmin = True
            db.commit()
            print("User updated.")

        print("\n" + "="*30)
        print("SUPER ADMIN CREDENTIALS:")
        print(f"Branch:   {branch_name}")
        print(f"Email:    {email}")
        print(f"Password: {password}")
        print("="*30 + "\n")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_initial_data()
