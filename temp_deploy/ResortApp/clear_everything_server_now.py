
from app.database import SessionLocal
from sqlalchemy import text
import sys

def clear_all_data():
    db = SessionLocal()
    try:
        print("Starting DEEP TRANSACTIONAL CLEANUP...")
        
        # Order of tables (some depend on others, but CASCADE helps)
        tables_to_truncate = [
            # Accounting
            "journal_entry_lines",
            "journal_entries",
            "payments",
            "expenses",
            "salary_payments",
            
            # Inventory & Stock
            "inventory_transactions",
            "purchase_details",
            "purchase_masters",
            "stock_issue_details",
            "stock_issues",
            "stock_requisition_details",
            "stock_requisitions",
            "waste_logs",
            "laundry_logs",
            "location_stocks",
            "asset_registry",
            "asset_mappings",
            
            # Bookings
            "booking_rooms",
            "bookings",
            "package_booking_rooms",
            "package_bookings",
            
            # Services & Food
            "employee_inventory_assignments",
            "assigned_services",
            "service_requests",
            "food_order_items",
            "food_orders",
            
            # Checkout
            "checkout_verifications",
            "checkout_payments",
            "checkouts",
            "checkout_requests",
            
            # Miscellaneous
            "notifications",
            "user_activities",
            "working_logs",
            "attendances",
            "leaves",
            "signatures",
            "work_orders"
        ]
        
        # Disable constraints briefly to speed up and avoid some issues
        db.execute(text("SET session_replication_role = 'replica';"))
        
        for table in tables_to_truncate:
            try:
                # Check if table exists before truncating
                result = db.execute(text(f"SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = '{table}')"))
                if result.fetchone()[0]:
                    db.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
                    print(f"✓ Cleared {table}")
                else:
                    # Try a simple delete if it's not a standard table or some issue
                    db.execute(text(f"DELETE FROM {table}"))
                    print(f"✓ Deleted from {table}")
            except Exception as e:
                print(f"  ⚠ Skipped {table}: {e}")
                db.rollback()
        
        # Reset inventory item stocks
        print("\nResetting inventory item stocks to 0...")
        db.execute(text("UPDATE inventory_items SET current_stock = 0"))
        
        # Reset room statuses
        print("Resetting all rooms to 'Available'...")
        db.execute(text("UPDATE rooms SET status = 'Available'"))
        
        # Re-enable constraints
        db.execute(text("SET session_replication_role = 'origin';"))
        
        db.commit()
        print("\n✅ TRANSACTIONAL DATA CLEARANCE COMPLETE!")
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clear_all_data()
