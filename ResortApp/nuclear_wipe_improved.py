from app.database import SessionLocal
from sqlalchemy import text
import sys

def nuclear_wipe():
    db = SessionLocal()
    try:
        print("=== STARTING NUCLEAR DATA WIPE (Transactional Only) ===")
        
        # Order matters less with CASCADE but let's list them all
        tables = [
            "journal_entry_lines", "journal_entries",
            "bill_items", "bills",
            "service_requests",
            "food_order_items", "food_orders",
            "employee_inventory_assignments", "assigned_services",
            "checkouts", "checkout_verifications", "checkout_payments", "checkout_requests",
            "booking_rooms", "package_booking_rooms", "package_bookings", "bookings",
            "asset_registry", "asset_mappings",
            "waste_logs",
            "stock_issue_details", "stock_issues",
            "stock_requisition_details", "stock_requisitions",
            "purchase_details", "purchase_masters",
            "inventory_transactions",
            "location_stocks",
            "notifications"
        ]
        
        # Check which tables exist before truncating
        existing_tables = []
        for table in tables:
            try:
                db.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                existing_tables.append(table)
            except Exception:
                db.rollback()
                continue
        
        if existing_tables:
            truncate_query = f"TRUNCATE TABLE {', '.join(existing_tables)} CASCADE;"
            print(f"Executing: {truncate_query}")
            db.execute(text(truncate_query))
            print("Truncate successful.")
        
        # Reset inventory stocks
        print("Resetting inventory stocks to 0...")
        db.execute(text("UPDATE inventory_items SET current_stock = 0"))
        
        # Reset room statuses
        print("Resetting room statuses to Available...")
        db.execute(text("UPDATE rooms SET status = 'Available'"))
        
        db.commit()
        print("=== NUCLEAR WIPE COMPLETE ===")
        
    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    nuclear_wipe()
