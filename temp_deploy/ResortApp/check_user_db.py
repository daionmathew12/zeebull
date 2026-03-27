from app.database import SessionLocal
from app.models.user import User
from app.utils.auth import verify_password
import sys

def check_user(email):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"User {email} NOT found in database.")
            # List some users to see what's there
            users = db.query(User).limit(5).all()
            print("Existing users (up to 5):")
            for u in users:
                print(f"- {u.email} (Role: {u.role.name if u.role else 'None'})")
            return
        
        print(f"User {email} found.")
        print(f"ID: {user.id}")
        print(f"Active: {user.is_active}")
        print(f"Role: {user.role.name if user.role else 'None'}")
        print(f"Hashed Password: {user.hashed_password}")
        
        # Check password '1234'
        is_valid = verify_password("1234", user.hashed_password)
        print(f"Password '1234' is valid: {is_valid}")
        
    finally:
        db.close()

if __name__ == "__main__":
    email = "a@h.com"
    if len(sys.argv) > 1:
        email = sys.argv[1]
    check_user(email)
