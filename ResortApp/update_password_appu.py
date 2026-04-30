import sys
import os

# Add the current directory to sys.path so we can import 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.user import User
from app.utils.auth import get_password_hash

def update_password(email, new_password):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"User {email} not found")
            # List all users to help debug
            all_users = db.query(User).all()
            print("Available users:")
            for u in all_users:
                print(f"- {u.email}")
            return
        
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        print(f"Password updated successfully for {email}")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_password("appu@gmail.com", "1234")
