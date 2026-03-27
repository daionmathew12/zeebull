
import sys
import os
sys.path.append(os.getcwd())
# Also append server path for when running on server
sys.path.append('/var/www/inventory/ResortApp')

from app.database import SessionLocal, engine
from sqlalchemy import text

def reset_database():
    db = SessionLocal()
    try:
        print("Starting Database Reset (Preserving Admin & Master Data)...")
        
        # 1. Operational Data
        print("Clearing Checkout Data...")
        db.execute(text("TRUNCATE TABLE checkout_verification_consumables CASCADE"))
        db.execute(text("TRUNCATE TABLE checkout_verification_damages CASCADE"))
        db.execute(text("TRUNCATE TABLE checkout_verifications CASCADE"))
        db.execute(text("TRUNCATE TABLE checkout_payments CASCADE"))
        db.execute(text("TRUNCATE TABLE checkouts CASCADE"))
        db.execute(text("TRUNCATE TABLE checkout_requests CASCADE"))
        
        print("Clearing Service/Food/Room Data...")
        db.execute(text("TRUNCATE TABLE room_consumables CASCADE"))
        db.execute(text("TRUNCATE TABLE assigned_services CASCADE"))
        db.execute(text("TRUNCATE TABLE food_order_items CASCADE"))
        db.execute(text("TRUNCATE TABLE food_orders CASCADE"))
        
        print("Clearing Bookings...")
        db.execute(text("TRUNCATE TABLE booking_rooms CASCADE"))
        db.execute(text("TRUNCATE TABLE bookings CASCADE"))
        db.execute(text("TRUNCATE TABLE package_booking_rooms CASCADE"))
        db.execute(text("TRUNCATE TABLE package_bookings CASCADE"))
        
        print("Clearing Inventory Operations...")
        db.execute(text("TRUNCATE TABLE stock_issue_details CASCADE"))
        db.execute(text("TRUNCATE TABLE stock_issues CASCADE"))
        db.execute(text("TRUNCATE TABLE inventory_transactions CASCADE"))
        db.execute(text("TRUNCATE TABLE location_stock CASCADE")) # Reset all stock counts
        
        print("Clearing Purchases & Expenses...")
        db.execute(text("TRUNCATE TABLE purchase_items CASCADE"))
        db.execute(text("TRUNCATE TABLE purchases CASCADE"))
        db.execute(text("TRUNCATE TABLE expenses CASCADE"))
        
        print("Clearing Staff (Attendance/Users)...")
        db.execute(text("TRUNCATE TABLE attendance CASCADE"))
        # Clear Users but KEEP ADMIN (and maybe yourself if needed, but 'except admin login' usually means just 'admin')
        # Assuming admin username is 'admin' or id 1. Let's try to keep both safety checks.
        db.execute(text("DELETE FROM users WHERE username != 'admin' AND role_id != (SELECT id FROM roles WHERE name='Admin' LIMIT 1)")) 
        
        # Cleanup orphaned notifications if any
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
