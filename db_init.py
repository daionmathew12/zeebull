import sys
import os
from sqlalchemy import create_engine, text
from passlib.context import CryptContext

# Set up paths 
sys.path.append("/var/www/zeebull/ResortApp")
os.chdir("/var/www/zeebull/ResortApp")

from app.database import engine, Base, SQLALCHEMY_DATABASE_URL
import app.models

def init_db():
    print(f"Connecting to {SQLALCHEMY_DATABASE_URL[:20]}...")
    
    # Create all tables
    print("Creating all tables from models...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created.")

    # Seed Admin Role and User
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        from app.models.user import Role, User
        from app.models.branch import Branch
        
        # Seed Default Branch
        default_branch = db.query(Branch).filter(Branch.id == 1).first()
        if not default_branch:
            print("Seeding default branch...")
            default_branch = Branch(
                id=1,
                name="Main Branch",
                code="MAIN",
                address="Default Address",
                phone="0000000000",
                email="main@orchid.com"
            )
            db.add(default_branch)
            db.commit()
            db.refresh(default_branch)
            print("✓ Default branch created.")
        
        if not db.query(Role).filter(Role.name == "admin").first():
            print("Seeding admin role...")
            admin_permissions = '["/dashboard","/bookings","/rooms","/users","/services","/expenses","/food-orders","/food-categories","/food-items","/billing","/account","/Userfrontend_data","/packages","/report","/guestprofiles","/user-history","/employee-management","/employee-dashboard","/inventory","/settings","/branch-management","/activity-logs","/laundry"]'
            admin_role = Role(name="admin", permissions=admin_permissions, branch_id=1)
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
            print(f"✓ Admin role created (ID: {admin_role.id})")
            
            # Seed other roles
            for rname in ['housekeeping', 'kitchen', 'waiter', 'maintenance']:
                 db.add(Role(name=rname, permissions='["/employee-dashboard"]', branch_id=1))
            db.commit()
            
            admin_role_id = admin_role.id
        else:
            admin_role_id = db.query(Role).filter(Role.name == "admin").first().id
            print("- Admin role already exists.")

        # Seed Super Admin User
        if not db.query(User).filter(User.email == "admin@orchid.com").first():
            print("Seeding superadmin user...")
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            hashed_password = pwd_context.hash("admin123")
            
            super_admin = User(
                email="admin@orchid.com",
                hashed_password=hashed_password,
                name="Super Admin",
                is_active=True,
                is_superadmin=True,
                role_id=admin_role_id,
                branch_id=None
            )
            db.add(super_admin)
            db.commit()
            print("✓ Superadmin created: admin@orchid.com / admin123")
        else:
            print("- Superadmin already exists.")

    except Exception as e:
        print(f"Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
