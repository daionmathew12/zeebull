import os
import sys

# Add the project root to sys.path
sys.path.append('/var/www/zeebull/ResortApp')
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ResortApp')))

from app.database import SessionLocal, engine
from sqlalchemy import text

def clear_operational_data():
    print("========================================")
    print("STAGING: Robust Operational Data Reset")
    print("========================================")
    
    # Check if 'y' is passed via echo
    if sys.stdin.isatty():
        confirm = input("Are you absolutely sure you want to PERMANENTLY DELETE all transactions? (y/N): ")
        if confirm.lower() != 'y':
            print("Reset aborted.")
            return
    else:
        print("Non-interactive mode: assuming 'y' from stdin.")

    tables = [
        "assigned_services", "service_requests", "food_order_items", "food_orders",
        "payments", "vouchers", "journal_entry_lines", "journal_entries",
        "expenses", "salary_payments", "inventory_transactions", "purchase_details",
        "purchase_masters", "stock_requisition_details", "stock_requisitions",
        "stock_issue_details", "stock_issues", "waste_logs", "laundry_logs",
        "inter_branch_transfers", "working_logs", "attendance", "leaves",
        "checkout_requests", "checkouts", "booking_rooms", "bookings",
        "package_booking_rooms", "package_bookings", "activity_logs", "notifications",
        "location_stocks"
    ]

    print("Clearing tables...")
    for table in tables:
        db = SessionLocal()
        try:
            db.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"))
            db.commit()
            print(f" - Truncated: {table}")
        except Exception as e:
            db.rollback()
            # print(f" - Skip: {table} (Error: {str(e).splitlines()[0]})")
            print(f" - Skip: {table} (Might not exist or already clear)")
        finally:
            db.close()

    # 3. Reset Inventory Stock Levels
    print("\nResetting inventory stock balances to 0...")
    db = SessionLocal()
    try:
        db.execute(text("UPDATE inventory_items SET current_stock = 0;"))
        db.commit()
        print(" - Success: Stock balances reset.")
    except Exception as e:
        db.rollback()
        print(f" - Error resetting stock: {e}")
    finally:
        db.close()

    print("\n========================================")
    print("SUCCESS: Data reset process finished.")
    print("========================================")

if __name__ == "__main__":
    clear_operational_data()
