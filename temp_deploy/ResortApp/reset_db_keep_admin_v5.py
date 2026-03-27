
import sys
import os
sys.path.append(os.getcwd())
sys.path.append('/var/www/inventory/ResortApp')

from app.database import SessionLocal, engine
from sqlalchemy import text

def reset_database():
    db = SessionLocal()
    try:
        print("Starting Database Reset (Preserving Admin & Master Data)...")
        
        # 1. Operational Data - Checkout
        print("Clearing Checkout Data...")
        db.execute(text("TRUNCATE TABLE checkout_verifications CASCADE"))
        db.execute(text("TRUNCATE TABLE checkout_payments CASCADE"))
        db.execute(text("TRUNCATE TABLE checkouts CASCADE"))
        db.execute(text("TRUNCATE TABLE checkout_requests CASCADE"))
        db.commit() # Commit Checkouts
        
        print("Clearing Service/Food/Room Data...")
        db.execute(text("TRUNCATE TABLE assigned_services CASCADE"))
        db.execute(text("TRUNCATE TABLE food_order_items CASCADE"))
        db.execute(text("TRUNCATE TABLE food_orders CASCADE"))
        db.execute(text("TRUNCATE TABLE laundry_logs CASCADE"))
        db.execute(text("TRUNCATE TABLE waste_logs CASCADE"))
        db.commit() # Commit Services
        
        print("Clearing Bookings...")
        db.execute(text("TRUNCATE TABLE booking_rooms CASCADE"))
        db.execute(text("TRUNCATE TABLE bookings CASCADE"))
        db.execute(text("TRUNCATE TABLE package_booking_rooms CASCADE"))
        db.execute(text("TRUNCATE TABLE package_bookings CASCADE"))
        db.commit() # Commit Bookings
        
        print("Clearing Inventory Operations...")
        db.execute(text("TRUNCATE TABLE stock_issue_details CASCADE"))
        db.execute(text("TRUNCATE TABLE stock_issues CASCADE"))
        db.execute(text("TRUNCATE TABLE stock_requisition_details CASCADE"))
        db.execute(text("TRUNCATE TABLE stock_requisitions CASCADE"))
        db.execute(text("TRUNCATE TABLE inventory_transactions CASCADE"))
        db.execute(text("TRUNCATE TABLE location_stocks CASCADE")) 
        db.execute(text("TRUNCATE TABLE asset_mappings CASCADE"))
        db.execute(text("TRUNCATE TABLE asset_registry CASCADE"))
        db.commit() # Commit Inventory
        
        print("Clearing Purchases & Expenses...")
        db.execute(text("TRUNCATE TABLE purchase_details CASCADE"))
        db.execute(text("TRUNCATE TABLE purchase_masters CASCADE"))
        db.execute(text("TRUNCATE TABLE expenses CASCADE"))
        db.commit() # Commit Purchases
        
        print("Clearing Staff...")
        tables_to_clear_staff = ["attendances", "leaves", "working_logs"]
        for t in tables_to_clear_staff:
            try:
                db.execute(text(f"TRUNCATE TABLE {t} CASCADE"))
            except Exception as e:
                print(f"Skipping {t} (Not Found or Error)")
                db.rollback() 
        
        db.commit()
        
        print("Clearing Non-Admin Users & Employees...")
        
        # 1. Delete employees linked to non-admin users
        # NOTE: Using text params is safer but for this fixed query literal is OK
        db.execute(text("""
            DELETE FROM employees 
            WHERE user_id IN (
                SELECT id FROM users 
                WHERE username != 'admin' 
                AND role_id != (SELECT id FROM roles WHERE name='Admin' LIMIT 1)
            ) 
            OR user_id IS NULL
        """))
        
        # 2. Delete non-admin users
        db.execute(text("DELETE FROM users WHERE username != 'admin' AND role_id != (SELECT id FROM roles WHERE name='Admin' LIMIT 1)")) 
        
        try:
             db.execute(text("TRUNCATE TABLE notifications CASCADE"))
        except: pass

        db.commit()
        print("Database Reset Complete. Admin user preserved.")
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_database()
