import sys
import os
import json

# Add the current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.user import Role

def check_role_permissions():
    db = SessionLocal()
    try:
        roles = db.query(Role).all()
        print(f"Found {len(roles)} roles:")
        for role in roles:
            print(f"\nRole: {role.name} (ID: {role.id}, Branch: {role.branch_id})")
            try:
                perms = json.loads(role.permissions) if role.permissions else []
                print(f"Permissions: {perms}")
            except Exception as e:
                print(f"Error parsing permissions: {e}")
                print(f"Raw permissions: {role.permissions}")
    finally:
        db.close()

if __name__ == "__main__":
    check_role_permissions()
