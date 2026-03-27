
import sys
import os
sys.path.append(os.getcwd())
sys.path.append('/var/www/inventory/ResortApp')

from app.database import SessionLocal
from sqlalchemy import text

def debug_and_nuke():
    db = SessionLocal()
    try:
        print("Checking leftover data counts...")
        
        tables_to_check = [
            "rooms", "packages", "services", "food_items", "inventory_items", 
            "bookings", "employees", "users"
        ]
        
        for t in tables_to_check:
            try:
                count = db.execute(text(f"SELECT count(*) FROM {t}")).scalar()
                print(f"Table '{t}': {count} rows")
            except Exception as e:
                print(f"Table '{t}' check failed: {e}")
        
        print("\nPerforming TARGETED NUKE on stubborn tables...")

        # 1. Manually find Admin ID to ensure we don't break logic (though TRUNCATE admin isn't the goal here)
        # We are handling tables 'rooms', 'packages' etc which have no user data usually.
        # But 'employees' and 'users' do.

        # Force Truncate stubborn tables
        stubborn = ["rooms", "packages", "services", "food_items", "inventory_categories", "inventory_items"]
        
        for t in stubborn:
            try:
                # Use CASCADE to wipe dependencies (like bookings linking to rooms) 
                db.execute(text(f"TRUNCATE TABLE {t} CASCADE"))
                db.commit() # Commit each individually
                print(f"✓ Truncated {t} SUCCESSFULLY")
            except Exception as e:
                print(f"❌ Failed to truncate {t}: {e}")
                db.rollback()

        print("\nFinal Check:")
        for t in tables_to_check:
            try:
                count = db.execute(text(f"SELECT count(*) FROM {t}")).scalar()
                print(f"Table '{t}': {count} rows")
            except: pass
            
    except Exception as e:
        print(f"Global Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_and_nuke()
