from app.database import engine, Base, SessionLocal
from sqlalchemy import text
from app.models.user import User, Role
from app.models.branch import Branch
from app.utils.auth import get_password_hash
import datetime

def wipe_db():
    print("--- WIPING ALL DATA FROM DATABASE ---")
    
    # 1. Drop and Recreate all tables (safest way to clear everything and reset IDs)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("[OK] All tables dropped and recreated.")
    
    # 2. Re-insert essential seeds (Role, Superadmin, Main Branch)
    db = SessionLocal()
    try:
        # Initial Branch
        main_branch = Branch(
            name="Orchid Main",
            code="MAIN",
            is_active=True
        )
        db.add(main_branch)
        db.flush()
        print(f"[SEED] Created 'Orchid Main' branch (ID: {main_branch.id})")
        
        # Initial Role
        admin_role = Role(
            name="Superadmin",
            permissions="all"
        )
        db.add(admin_role)
        db.flush()
        print(f"[SEED] Created 'Superadmin' role (ID: {admin_role.id})")
        
        # Initial Superadmin
        superadmin = User(
            email="admin@orchid.com",
            hashed_password=get_password_hash("admin123"),
            name="Orchid Admin",
            role_id=admin_role.id,
            branch_id=main_branch.id,
            is_superadmin=True,
            is_active=True
        )
        db.add(superadmin)
        db.commit()
        print(f"[SEED] Created superadmin 'admin@orchid.com' (Pass: admin123)")
        
    except Exception as e:
        print(f"[ERROR] Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("--- DATABASE WIPE & SEED COMPLETE ---")

if __name__ == "__main__":
    wipe_db()
