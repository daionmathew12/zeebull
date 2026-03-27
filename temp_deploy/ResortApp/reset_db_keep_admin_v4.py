
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
        db.execute(text("TRUNCATE TABLE location_stocks CASCADE")) 
        db.execute(text("TRUNCATE TABLE asset_mappings CASCADE"))
        db.execute(text("TRUNCATE TABLE asset_registry CASCADE"))
        
        print("Clearing Purchases & Expenses...")
        db.execute(text("TRUNCATE TABLE purchase_details CASCADE"))
        db.execute(text("TRUNCATE TABLE purchase_masters CASCADE"))
        db.execute(text("TRUNCATE TABLE expenses CASCADE"))
        
        print("Clearing Staff...")
        # Check for both singular and plural mostly seen 'attendances' in employee.py
        # But 'attendance' in my first thought. I'll try both to be safe or check explicitly.
        # But TRUNCATE will fail if table doesn't exist.
        # I'll rely on CASCADE from employees if possible, or try/except blocks.
        
        tables_to_clear_staff = ["attendances", "attendance", "leaves", "working_logs", "salary_payments"]
        for t in tables_to_clear_staff:
            try:
                db.execute(text(f"TRUNCATE TABLE {t} CASCADE"))
            except Exception as e:
                # print(f"Skipping {t}: {e}")
                db.rollback() # Important to rollback if failed to proceed
                # Re-open session or just ensure transaction valid?
                # Rolling back the specific error.
                pass
        
        # Clear Employees (except those linked to Admin if any, but simplified: Clear all non-admin employees)
        # Assuming Admin User ID=1 or Username='admin'
        # First we clear the employees table rows that are NOT the admin user's employee profile
        # But finding the admin's employee profile is hard if not linked.
        # Safest: Delete employees where user_id refers to non-admin or is null?
        
        print("Clearing Non-Admin Users & Employees...")
        
        # 1. Unlink employees from users to be deleted? No, just delete employees first.
        # Delete employees linked to users who are NOT admin
        # Also delete employees with NO user (orphaned)
        db.execute(text("""
            DELETE FROM employees 
            WHERE user_id IN (
                SELECT id FROM users 
                WHERE username != 'admin' 
                AND role_id != (SELECT id FROM roles WHERE name='Admin' LIMIT 1)
            ) 
            OR user_id IS NULL
        """))
        
        # 2. Now Delete the Users
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
