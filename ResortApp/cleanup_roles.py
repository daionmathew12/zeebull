import sys
sys.path.append('.')
from sqlalchemy import func
from app.database import SessionLocal
from app.models.user import Role, User

def cleanup_duplicate_roles():
    db = SessionLocal()
    try:
        # Find duplicates grouped by lowercase name and branch_id
        duplicates = db.query(
            func.lower(Role.name).label('lname'), 
            Role.branch_id, 
            func.count(Role.id)
        ).group_by(
            func.lower(Role.name), 
            Role.branch_id
        ).having(func.count(Role.id) > 1).all()

        if not duplicates:
            print("No duplicate roles found.")
            return

        print(f"Found {len(duplicates)} sets of duplicate roles.")

        for name_lower, branch_id, count in duplicates:
            print(f"Processing '{name_lower}' in Branch {branch_id} ({count} instances)")
            
            # Fetch all matching instances, ordered by ID (keep the oldest)
            instances = db.query(Role).filter(
                func.lower(Role.name) == name_lower,
                Role.branch_id == branch_id
            ).order_by(Role.id).all()
            
            if len(instances) <= 1:
                continue
                
            primary_role = instances[0]
            duplicate_roles = instances[1:]
            
            print(f"  Keeping primary role ID {primary_role.id} ('{primary_role.name}')")
            
            for dup in duplicate_roles:
                print(f"  Migrating users from duplicate role ID {dup.id} ('{dup.name}')")
                
                # Update users attached to the duplicate role
                users_to_update = db.query(User).filter(User.role_id == dup.id).all()
                for user in users_to_update:
                    print(f"    - Moving user {user.email} (ID {user.id})")
                    user.role_id = primary_role.id
                
                # Delete the duplicate role
                print(f"  Deleting duplicate role ID {dup.id}")
                db.delete(dup)
                
            # Commit changes for this set
            db.commit()
            print(f"Successfully cleaned up duplicates for '{name_lower}'")

    except Exception as e:
        print(f"Error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_duplicate_roles()
