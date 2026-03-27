
import os
import sys
from sqlalchemy import create_engine, text

def get_db_url():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        env_path = os.path.join(os.getcwd(), ".env")
    if not os.path.exists(env_path):
        env_path = os.path.join(os.getcwd(), "ResortApp", ".env")
    
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("DATABASE_URL="):
                    return line.split("=", 1)[1].strip()
    return None

TABLES_TO_CLEAR = [
    "activity_logs", "bookings", "booking_rooms", "package_bookings", 
    "package_booking_rooms", "checkouts", "checkout_payments", 
    "checkout_verification", "checkout_requests", "service_requests", 
    "food_orders", "food_order_items", "inventory_transactions", 
    "stock_issues", "stock_issue_details", "stock_requisitions", 
    "stock_requisition_details", "stock_movements", "stock_usage", 
    "stock_levels", "location_stocks", "outlet_stocks", "linen_stocks", 
    "purchase_masters", "purchase_details", "purchase_orders", "po_items", 
    "purchase_entries", "purchase_entry_items", "goods_received_notes", 
    "grn_items", "wastage_logs", "waste_logs", "expenses", 
    "inventory_expenses", "notifications", "working_logs", 
    "maintenance_tickets", "work_orders", "work_order_parts", 
    "work_order_part_issues", "lost_found", "laundry_services", 
    "linen_movements", "linen_wash_logs", "room_consumable_assignments", 
    "room_inventory_audits", "journal_entries", "journal_entry_lines", 
    "vouchers", "payments", "key_movements", "guest_suggestions", 
    "fire_safety_incidents", "fire_safety_inspections", 
    "fire_safety_maintenance", "security_maintenance", 
    "security_uniforms", "restock_alerts", "expiry_alerts", 
    "eod_audits", "eod_audit_items", "perishable_batches", 
    "indent_items", "indents", "accounting_ledgers", 
    "assigned_services", "employee_inventory_assignments", 
    "leaves", "attendances", "salary_payments", "service_charges"
]

def clear_data(db_url):
    if not db_url:
        print("Error: Could not find DATABASE_URL")
        return

    # Check if URL starts with postgresql+psycopg2 and convert to postgresql
    if db_url.startswith("postgresql+psycopg2://"):
        db_url = db_url.replace("postgresql+psycopg2://", "postgresql://")

    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            # Get list of existing tables in the database
            existing_tables_result = conn.execute(text(
                "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public';"
            ))
            existing_tables = [row[0] for row in existing_tables_result]
            
            tables_to_truncate = [t for t in TABLES_TO_CLEAR if t in existing_tables]
            
            if not tables_to_truncate:
                print("No matching tables found to clear.")
            else:
                print(f"=== DELETING OPERATIONAL DATA FROM DATABASE ===")
                table_list_str = ", ".join(['"' + t + '"' for t in tables_to_truncate])
                truncate_query = f"TRUNCATE TABLE {table_list_str} RESTART IDENTITY CASCADE"
                
                conn.execute(text(truncate_query))
                conn.commit()
                print(f"  Successfully cleared {len(tables_to_truncate)} tables.")
            
            # Reset specific statuses
            print("\n=== RESETTING MASTER DATA STATUSES ===")
            if "rooms" in existing_tables:
                print("  - Resetting Room status to 'Available'...")
                conn.execute(text("UPDATE rooms SET status = 'Available', housekeeping_status = 'Clean', housekeeping_updated_at = NULL"))
            
            if "inventory_items" in existing_tables:
                print("  - Resetting Inventory Item stock to 0...")
                conn.execute(text("UPDATE inventory_items SET current_stock = 0.0"))
            
            conn.commit()
            print("\n=== SYSTEM DATA CLEARED SUCCESSFULLY ===")
            
    except Exception as e:
        print(f"\n[ERROR] Cleanup Failed: {str(e)}")

if __name__ == "__main__":
    db_url = get_db_url()
    if not db_url:
        if len(sys.argv) > 1:
            db_url = sys.argv[1]
    
    clear_data(db_url)
