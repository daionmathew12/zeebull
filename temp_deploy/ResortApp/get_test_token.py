from app.database import SessionLocal
from app.models.user import User, Role
from app.utils.auth import create_access_token
import sys

def get_admin_token():
    db = SessionLocal()
    try:
        admin_role = db.query(Role).filter(Role.name == 'admin').first()
        if not admin_role:
             print("No admin role found")
             return
        admin_user = db.query(User).filter(User.role_id == admin_role.id).first()
        if not admin_user:
             print("No admin user found")
             return
        
        # Token payload expects 'user_id' based on get_current_user implementation
        token = create_access_token(data={'user_id': admin_user.id, 'sub': admin_user.email})
        print(token)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    get_admin_token()
