
import sys
import os
sys.path.append(os.getcwd())
sys.path.append('/var/www/inventory/ResortApp')

from app.database import SessionLocal
from sqlalchemy import text
from app.models.room import Room
# Dynamic import to avoid errors if file names vary
try: from app.models.Package import Package 
except: pass
try: from app.models.packages import Package
except: pass
try: from app.models.service import Service
except: pass
try: from app.models.food_item import FoodItem
except: pass

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
        
        # 1. Clear packages (Case sensitivity check? 'Package' vs 'packages')
        # Postgres table names are usually lowercase.
        
        # We will use a massive TRUNCATE CASCADE.
        # But we must be careful not to delete the admin user.
        
        # Identify Admin ID first
        admin_id_query = text("SELECT id FROM users WHERE email='admin@orchid.com' OR username='admin' LIMIT 1")
        admin_id = db.execute(admin_id_query).scalar()
        print(f"Preserving Admin ID: {admin_id}")

        # Targeted Truncates with Commit in between to avoid rollback loops
        
        # Group 1: The stubborn ones
        target_tables = [
            "rooms", 
            "packages", 
            "services", 
            "food_items", 
            "food_categories",
            "inventory_items",
            "inventory_categories"
        ]
        
        for t in target_tables:
            try:
                db.execute(text(f"TRUNCATE TABLE {t} CASCADE"))
                db.commit() # Commit IMMEDIATELY
                print(f"✓ Truncated {t}")
            except Exception as e:
                print(f"❌ Failed to truncate {t}: {e}")
                db.rollback()
                
        # Group 2: Final sweep of dependent operational tables
        op_tables = [
            "assigned_services", "booking_rooms", "bookings", 
            "package_booking_rooms", "package_bookings"
        ]
        for t in op_tables:
             try:
                db.execute(text(f"TRUNCATE TABLE {t} CASCADE"))
                db.commit()
             except: 
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
