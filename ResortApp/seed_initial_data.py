from app.database import SessionLocal
from app.models.branch import Branch
from app.models.user import Role
import json

def seed():
    db = SessionLocal()
    try:
        # 1. Seed Default Branch
        branch = db.query(Branch).filter(Branch.id == 1).first()
        if not branch:
            branch = Branch(
                id=1,
                name="Main Branch",
                code="MAIN",
                is_active=True
            )
            db.add(branch)
            db.commit()
            print("Default branch seeded.")
        
        # 2. Ensure roles are seeded (if not already)
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
            print("Admin role seeded.")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
