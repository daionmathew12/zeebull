from app.database import SessionLocal
from app.models.user import User, Role
from app.models.branch import Branch
from app.utils.auth import get_password_hash
import json

def create_superadmin():
    db = SessionLocal()
    try:
        # Ensure admin role exists (Global/Branch-agnostic)
        admin_role = db.query(Role).filter(Role.name == "admin", Role.branch_id == None).first()
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
            db.refresh(admin_role)

        # Check for admin@orchid.com
        user = db.query(User).filter(User.email == "admin@orchid.com").first()
        if not user:
            user = User(
                name="Super Admin",
                email="admin@orchid.com",
                hashed_password=get_password_hash("admin123"),
                role_id=admin_role.id,
                is_active=True,
                is_superadmin=True
            )
            db.add(user)
        else:
            user.is_superadmin = True
            user.hashed_password = get_password_hash("admin123")
            user.role_id = admin_role.id
        
        db.commit()
        print("Super Admin verified/created:")
        print("Email: admin@orchid.com")
        print("Password: admin123")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_superadmin()
