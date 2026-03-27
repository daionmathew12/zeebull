from sqlalchemy import create_engine, text
from app.database import Base, engine
from app.models import *
import json
from app.utils.auth import get_password_hash
from app.models.user import User, Role
from app.models.branch import Branch
from sqlalchemy.orm import Session

def setup_local():
    print("Initializing Database...")
    Base.metadata.create_all(bind=engine)
    
    db = Session(bind=engine)
    try:
        # Seed Branch
        branch = db.query(Branch).filter(Branch.id == 1).first()
        if not branch:
            branch = Branch(id=1, name="Main Branch", code="MAIN", is_active=True)
            db.add(branch)
            db.commit()
            print("Branch 1 created.")
            
        # Seed Admin Role
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            perms = [
                "/dashboard", "/bookings", "/rooms", "/services", "/expenses", 
                "/food-orders", "/food-categories", "/food-items", "/billing", 
                "/packages", "/users", "/roles", "/employees", "/reports", 
                "/account", "/userfrontend_data", "/guestprofiles", "/employee-management",
                "/branch-management"
            ]
            admin_role = Role(name="admin", permissions=json.dumps(perms), branch_id=None)
            db.add(admin_role)
            db.commit()
            print("Admin role created.")
            
        # Seed Super Admin
        user = db.query(User).filter(User.email == "admin@orchid.com").first()
        if not user:
            user = User(
                name="Super Admin",
                email="admin@orchid.com",
                hashed_password=get_password_hash("admin123"),
                role_id=admin_role.id,
                is_active=True,
                is_superadmin=True,
                branch_id=None
            )
            db.add(user)
            db.commit()
            print("Super Admin created: admin@orchid.com / admin123")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    setup_local()
