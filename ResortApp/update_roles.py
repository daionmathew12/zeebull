import sys
import os
import json

# Add the current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.user import Role

def update_role_permissions():
    db = SessionLocal()
    try:
        # Update Kitchen role
        kitchen_role = db.query(Role).filter(Role.name == "kitchen").first()
        if kitchen_role:
            perms = json.loads(kitchen_role.permissions) if kitchen_role.permissions else []
            new_perms = ["rooms:view", "employees:view"]
            for p in new_perms:
                if p not in perms:
                    perms.append(p)
            kitchen_role.permissions = json.dumps(perms)
            print(f"Updated Kitchen role permissions: {perms}")
        
        # Update HouseKeeping role
        housekeeping_role = db.query(Role).filter(Role.name == "HouseKeeping").first()
        if housekeeping_role:
            perms = json.loads(housekeeping_role.permissions) if housekeeping_role.permissions else []
            new_perms = ["employees:view"]
            for p in new_perms:
                if p not in perms:
                    perms.append(p)
            housekeeping_role.permissions = json.dumps(perms)
            print(f"Updated HouseKeeping role permissions: {perms}")
            
        db.commit()
        print("Role permissions updated successfully.")
    except Exception as e:
        print(f"Error updating role permissions: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_role_permissions()
