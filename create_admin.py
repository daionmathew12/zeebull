import os
import sys

# Configure exact path to app
sys.path.insert(0, '/var/www/zeebull/ResortApp')

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User, Role
from app.models.branch import Branch

def create_superadmin():
    db = SessionLocal()
    try:
        # 1. Create a default branch if none exist
        print("Checking for branches...")
        branch = db.query(Branch).first()
        if not branch:
            print("Creating default branch...")
            branch = Branch(name="Main Branch", code="MAIN")
            db.add(branch)
            db.commit()
            db.refresh(branch)
            print(f"Created branch with ID: {branch.id}")

        # 2. Check for admin role
        print("Checking for admin role...")
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            admin_role = Role(name="admin", branch_id=branch.id)
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
            print(f"Created new admin role with ID: {admin_role.id}")

        # 3. Create super admin
        existing_superadmin = db.query(User).filter(User.email == "admin@zeebull.com").first()
        if existing_superadmin:
            print(f"Superadmin already exists with ID: {existing_superadmin.id}")
            existing_superadmin.is_superadmin = True
            db.commit()
            print("Successfully updated existing user to superadmin status.")
            return

        print("Creating new superadmin...")
        from app.utils.auth import get_password_hash
        # Use name and email as they are defined in the schema
        new_user = User(
            name="Super Admin",
            email="admin@zeebull.com",
            hashed_password=get_password_hash("Admin@123"),
            is_active=True,
            is_superadmin=True,
            role_id=admin_role.id,
            branch_id=branch.id
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        print(f"✅ Superadmin created successfully!")
        print(f"Email: admin@zeebull.com")
        print(f"Password: Admin@123")
        
    except Exception as e:
        print(f"❌ Error creating superadmin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_superadmin()
