import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database configuration
DATABASE_URL = "postgresql+psycopg2://postgres:qwerty123@localhost:5432/zeebuldb"

def factory_reset():
    print("=" * 80)
    print("🚀 STARTING PRODUCTION FACTORY RESET")
    print("=" * 80)
    
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 1. Transactional Tables (TRUNCATE CASCADE)
        transactional_tables = [
            # Accounting
            "journal_entry_lines", "journal_entries", "payments", "expenses", "salary_payments",
            
            # Inventory & Stock
            "inventory_transactions", "purchase_details", "purchase_masters",
            "stock_issue_details", "stock_issues", "stock_requisition_details", "stock_requisitions",
            "waste_logs", "laundry_logs", "location_stocks", "asset_registry", "asset_mappings",
            
            # Bookings
            "booking_rooms", "bookings", "package_booking_rooms", "package_bookings",
            
            # Services & Food
            "employee_inventory_assignments", "assigned_services", "service_requests",
            "food_order_items", "food_orders",
            
            # Checkout
            "checkout_verifications", "checkout_payments", "checkouts", "checkout_requests",
            
            # Miscellaneous
            "notifications", "user_activities", "working_logs", "attendances", "leaves",
            "signatures", "work_orders"
        ]
        
        # 2. Master Tables (DELETE)
        master_tables_to_clear = [
            "service_images",
            "service_inventory_items",
            "laundry_services", # Just in case it's definitions
            "services",
            "signature_experiences"
        ]
        
        # Disable constraints briefly
        print("\n--- Disabling constraints ---")
        session.execute(text("SET session_replication_role = 'replica';"))
        
        # Truncate transactional tables
        print("\n--- Clearing Transactional Data ---")
        for table in transactional_tables:
            try:
                # Check if exists
                result = session.execute(text(f"SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = '{table}')"))
                if result.fetchone()[0]:
                    session.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
                    print(f"  ✓ Cleared {table}")
            except Exception as e:
                print(f"  ⚠ Failed to clear {table}: {e}")
                session.rollback()
        
        # Delete master data
        print("\n--- Clearing Master Service Data ---")
        for table in master_tables_to_clear:
            try:
                result = session.execute(text(f"SELECT EXISTS (SELECT FROM pg_tables WHERE tablename = '{table}')"))
                if result.fetchone()[0]:
                    session.execute(text(f"DELETE FROM {table}"))
                    print(f"  ✓ Deleted from {table}")
            except Exception as e:
                print(f"  ⚠ Failed to delete from {table}: {e}")
                session.rollback()
        
        # Reset inventory stocks
        print("\n--- Resetting inventory stocks to 0 ---")
        session.execute(text("UPDATE inventory_items SET current_stock = 0"))
        print("  ✓ Inventory stocks reset")
        
        # Reset room status
        print("\n--- Resetting room status to 'Available' ---")
        session.execute(text("UPDATE rooms SET status = 'Available'"))
        print("  ✓ Room status reset")
        
        # Re-enable constraints
        print("\n--- Re-enabling constraints ---")
        session.execute(text("SET session_replication_role = 'origin';"))
        
        session.commit()
        print("\n" + "=" * 80)
        print("✅ FACTORY RESET COMPLETE!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    factory_reset()
