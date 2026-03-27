
import sys
import os
sys.path.append(os.getcwd())
sys.path.append('/var/www/inventory/ResortApp')

from app.database import SessionLocal, engine
from app.models.user import User, Role
from sqlalchemy import text

def factory_reset():
    db = SessionLocal()
    try:
        print("Starting FACTORY RESET (Preserving Admin User & Roles)...")
        
        # 1. Identify Admin User to Preserve
        admin_email = "admin@orchid.com"
        admin_user = db.query(User).filter(User.email == admin_email).first()
        
        admin_id = None
        if admin_user:
            print(f"Found Admin User: {admin_user.name} (ID: {admin_user.id}) - WILL PRESERVE")
            admin_id = admin_user.id
        else:
            print("WARNING: Admin user 'admin@orchid.com' not found!")
            admin_user = db.query(User).filter(User.name == 'admin').first()
            if admin_user:
                print(f"Found User named 'admin': ID {admin_user.id} - WILL PRESERVE")
                admin_id = admin_user.id
        
        print("Clearing Operational & Master Data...")
        
        # List of tables to clear
        tables = [
             "checkout_verifications", "checkout_payments", "checkouts", "checkout_requests",
            "booking_rooms", "bookings", "package_booking_rooms", "package_bookings",
            "assigned_services", "food_order_items", "food_orders",
            "stock_issue_details", "stock_issues", "stock_requisition_details", "stock_requisitions",
            "inventory_transactions", "location_stocks", "asset_mappings", "asset_registry",
            "waste_logs", "laundry_logs", 
            "purchase_details", "purchase_masters", "expenses",
            "attendances", "leaves", "working_logs", 
            "notifications", # Clear notifications explicitly BEFORE deletions
            "salary_payments", "work_orders", "signatures", "user_activities",
            "inventory_items", "inventory_categories", 
            "rooms", "locations", 
            "food_items", "food_categories",
            "services", 
            "packages", 
            "vendors",
            "unit_conversions", "units_of_measurement"
        ]
        
        # Disable Triggers if possible (Postgres Specific)
        # db.execute(text("SET session_replication_role = 'replica';")) # Highly destructive/dangerous but effective
        
        # Force Clean Notifications first to avoid FK issues with User deletion
        db.execute(text("TRUNCATE TABLE notifications CASCADE"))
        
        for t in tables:
            try:
                if t != "notifications":
                     db.execute(text(f"TRUNCATE TABLE {t} CASCADE"))
                     # print(f"✓ Cleared {t}")
            except Exception as e:
                # print(f"  - Table {t} issue: {e}")
                db.rollback() 
        
        # Additional table catch-all just in case
        try:
             db.execute(text("TRUNCATE TABLE activities CASCADE"))
        except: pass
        
        db.commit()

        # 3. Clear Staff/Employees
        print("Clearing Employees...")
        if admin_id:
             db.execute(text(f"DELETE FROM employees WHERE user_id != {admin_id} OR user_id IS NULL"))
        else:
             db.execute(text("DELETE FROM employees"))
        
        # 4. Clear Users (Except Admin)
        print("Clearing Users...")
        # Check if notifications still hold references (even after truncate? unlikely, but session flush helps)
        
        if admin_id:
            # Explicit delete of notifications linked to users to be deleted? 
            # (TRUNCATE should have handled it, but let's be safe)
            db.execute(text(f"DELETE FROM notifications WHERE recipient_id != {admin_id} AND recipient_id IS NOT NULL"))
            
            db.execute(text(f"DELETE FROM users WHERE id != {admin_id}"))
        else:
             pass

        db.commit()
        print("Factory Reset Complete. Admin preserved.")
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    factory_reset()
