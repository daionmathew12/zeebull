
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
        
        print("Clearing Service/Food/Room Data...")
        db.execute(text("TRUNCATE TABLE assigned_services CASCADE"))
        db.execute(text("TRUNCATE TABLE food_order_items CASCADE"))
        db.execute(text("TRUNCATE TABLE food_orders CASCADE"))
        db.execute(text("TRUNCATE TABLE laundry_logs CASCADE"))
        db.execute(text("TRUNCATE TABLE waste_logs CASCADE"))
        
        print("Clearing Bookings...")
        db.execute(text("TRUNCATE TABLE booking_rooms CASCADE"))
        db.execute(text("TRUNCATE TABLE bookings CASCADE"))
        db.execute(text("TRUNCATE TABLE package_booking_rooms CASCADE"))
        db.execute(text("TRUNCATE TABLE package_bookings CASCADE"))
        
        print("Clearing Inventory Operations...")
        db.execute(text("TRUNCATE TABLE stock_issue_details CASCADE"))
        db.execute(text("TRUNCATE TABLE stock_issues CASCADE"))
        db.execute(text("TRUNCATE TABLE stock_requisition_details CASCADE"))
        db.execute(text("TRUNCATE TABLE stock_requisitions CASCADE"))
        db.execute(text("TRUNCATE TABLE inventory_transactions CASCADE"))
        db.execute(text("TRUNCATE TABLE location_stocks CASCADE")) # Corrected Plural
        db.execute(text("TRUNCATE TABLE asset_mappings CASCADE"))
        db.execute(text("TRUNCATE TABLE asset_registry CASCADE"))
        
        print("Clearing Purchases & Expenses...")
        db.execute(text("TRUNCATE TABLE purchase_details CASCADE")) # Corrected Name
        db.execute(text("TRUNCATE TABLE purchase_masters CASCADE")) # Corrected Name
        db.execute(text("TRUNCATE TABLE expenses CASCADE"))
        
        print("Clearing Staff (Attendance/Users)...")
        try:
             db.execute(text("TRUNCATE TABLE attendance CASCADE"))
             db.execute(text("TRUNCATE TABLE work_orders CASCADE")) # Likely exists
             db.execute(text("TRUNCATE TABLE working_logs CASCADE")) # Likely exists
        except: pass

        print("Clearing Non-Admin Users...")
        # Clear Users but KEEP Admin
        db.execute(text("DELETE FROM users WHERE username != 'admin' AND role_id != (SELECT id FROM roles WHERE name='Admin' LIMIT 1)")) 
        
        try:
             db.execute(text("TRUNCATE TABLE notifications CASCADE"))
        except: pass

        db.commit()
        print("Database Reset Complete. Admin user preserved.")
        
    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_database()
