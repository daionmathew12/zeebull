import sys
import os

# Add ResortApp to path
sys.path.append(os.path.join(os.getcwd(), 'ResortApp'))

from app.database import SessionLocal
from app.models.user import User
from app.models.branch import Branch
from sqlalchemy import text

def check():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print("Users:")
        for user in users:
            print(f"ID: {user.id}, Name: {user.name}, Email: {user.email}, Branch ID: {user.branch_id}, Super: {user.is_superadmin}")
            
        branches = db.query(Branch).all()
        print("\nBranches:")
        for b in branches:
            print(f"ID: {b.id}, Name: {b.name}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check()
