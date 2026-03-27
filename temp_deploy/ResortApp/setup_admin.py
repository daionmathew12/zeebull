import sys
import os
import json

# Add current directory to path so we can import app modules
sys.path.append(os.getcwd())

from app.database import SessionLocal, Base, engine
from app.models.user import User, Role
# Import the hash function used by the app to ensure compatibility
from app.utils.auth import get_password_hash

def init_db():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created.")

def create_admin():
    db = SessionLocal()
    try:
        # 1. Ensure 'admin' role exists (lowercase 'admin' to match api/auth.py checks)
        admin_role_name = "admin"
        admin_role = db.query(Role).filter(Role.name == admin_role_name).first()
        
        # Permissions as a JSON list
        perms = [
            "/dashboard", "/bookings", "/rooms", "/services", "/expenses", 
            "/food-orders", "/food-categories", "/food-items", "/billing", 
            "/packages", "/users", "/roles", "/employees", "/reports", 
            "/account", "/userfrontend_data", "/guestprofiles", "/employee-management"
        ]
        perms_json = json.dumps(perms)

        if not admin_role:
            print(f"Creating '{admin_role_name}' role...")
            admin_role = Role(
                name=admin_role_name,
                permissions=perms_json
            )
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
            print("Admin role created.")
        else:
            print(f"Role '{admin_role_name}' already exists. Updating permissions...")
            admin_role.permissions = perms_json
            db.commit()
        
        # 2. Ensure admin user exists
        email = "admin@orchid.com"
        password = "admin123"
        
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"Creating user '{email}'...")
            hashed_pwd = get_password_hash(password)
            user = User(
                name="System Admin",
                email=email,
                hashed_password=hashed_pwd,
                phone="1234567890",
                role_id=admin_role.id,
                is_active=True
            )
            db.add(user)
            db.commit()
            print("Admin user created.")
        else:
            print(f"User '{email}' already exists. Resetting password...")
            user.hashed_password = get_password_hash(password)
            user.role_id = admin_role.id
            user.is_active = True
            db.commit()
            print("Admin user password reset.")

        print("\n" + "="*30)
        print("ADMIN CREDENTIALS:")
        print(f"Email:    {email}")
        print(f"Password: {password}")
        print("="*30 + "\n")

    except Exception as e:
        print(f"Error creating admin: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    create_admin()
