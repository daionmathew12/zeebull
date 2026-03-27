"""
COMPREHENSIVE DATA CLEANUP SCRIPT - FINAL VERSION
Clears ALL transactional data, handling errors properly
"""
from app.database import SessionLocal
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

def safe_delete(db, table_name, description):
    """Safely delete from a table, skipping if it doesn't exist"""
    try:
        result = db.execute(text(f"DELETE FROM {table_name}"))
        count = result.rowcount
        print(f"   ✅ {description} cleared ({count} rows)")
        db.commit()  # Commit after each successful delete
        return True
    except ProgrammingError as e:
        db.rollback()  # Rollback on error
        if "does not exist" in str(e):
            print(f"   ⚠️  {description} - table doesn't exist, skipping")
            return False
        else:
            print(f"   ❌ {description} - error: {e}")
            return False

def clear_all_transactional_data():
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("⚠️  COMPREHENSIVE DATA CLEANUP - STARTING...")
        print("=" * 70)
        
        # Order matters due to foreign key constraints!
        
        # 1. Clear Checkout-related data
        print("\n1. Clearing checkout data...")
        safe_delete(db, "checkout_verifications", "Checkout verifications")
        safe_delete(db, "checkout_payments", "Checkout payments")
        safe_delete(db, "checkout_requests", "Checkout requests")
        
        # 2. Clear Billing/Invoices
        print("\n2. Clearing billing data...")
        safe_delete(db, "bill_items", "Bill items")
        safe_delete(db, "bills", "Bills")
        
        # 3. Clear Service Requests
        print("\n3. Clearing service requests...")
        safe_delete(db, "service_requests", "Service requests")
        
        # 4. Clear Food Orders
        print("\n4. Clearing food orders...")
        safe_delete(db, "food_order_items", "Food order items")
        safe_delete(db, "food_orders", "Food orders")
        
        # 5. Clear Assigned Services
        print("\n5. Clearing assigned services...")
        safe_delete(db, "employee_inventory_assignments", "Employee inventory assignments")
        safe_delete(db, "assigned_services", "Assigned services")
        
        # 6. Clear Bookings
        print("\n6. Clearing bookings...")
        safe_delete(db, "checkouts", "Checkouts")  # Must be before bookings
        safe_delete(db, "booking_rooms", "Booking rooms")
        safe_delete(db, "package_booking_rooms", "Package booking rooms")
        safe_delete(db, "package_bookings", "Package bookings")
        safe_delete(db, "bookings", "Bookings")
        
        # 7. Clear Asset Registry & Mappings
        print("\n7. Clearing asset registry & mappings...")
        safe_delete(db, "asset_registry", "Asset registry")
        safe_delete(db, "asset_mappings", "Asset mappings")
        
        # 8. Clear Waste Logs
        print("\n8. Clearing waste logs...")
        safe_delete(db, "waste_logs", "Waste logs")
        
        # 9. Clear Stock Issues
        print("\n9. Clearing stock issues...")
        safe_delete(db, "stock_issue_details", "Stock issue details")
        safe_delete(db, "stock_issues", "Stock issues")
        
        # 10. Clear Stock Requisitions
        print("\n10. Clearing stock requisitions...")
        safe_delete(db, "stock_requisition_details", "Stock requisition details")
        safe_delete(db, "stock_requisitions", "Stock requisitions")
        
        # 11. Clear Purchases
        print("\n11. Clearing purchases...")
        safe_delete(db, "purchase_details", "Purchase details")
        safe_delete(db, "purchase_masters", "Purchase masters")
        
        # 12. Clear Inventory Transactions
        print("\n12. Clearing inventory transactions...")
        safe_delete(db, "inventory_transactions", "Inventory transactions")
        
        # 13. Clear Location Stocks
        print("\n13. Clearing location stocks...")
        safe_delete(db, "location_stocks", "Location stocks")
        
        # 14. Reset Inventory Item Stocks to 0
        print("\n14. Resetting inventory item stocks to 0...")
        try:
            result = db.execute(text("UPDATE inventory_items SET current_stock = 0"))
            db.commit()
            print(f"   ✅ Inventory stocks reset to 0 ({result.rowcount} items)")
        except Exception as e:
            db.rollback()
            print(f"   ❌ Error resetting inventory stocks: {e}")
        
        # 15. Clear Accounting/Journal Entries
        print("\n15. Clearing accounting entries...")
        safe_delete(db, "journal_entry_lines", "Journal entry lines")
        safe_delete(db, "journal_entries", "Journal entries")
        
        # 16. Clear Notifications
        print("\n16. Clearing notifications...")
        safe_delete(db, "notifications", "Notifications")
        
        print("\n" + "=" * 70)
        print("✅ CLEANUP COMPLETE!")
        print("=" * 70)
        print("\nThe system has been reset to a clean state.")
        print("\nKEPT:")
        print("  ✅ Users/Login")
        print("  ✅ Inventory Items (stock = 0)")
        print("  ✅ Categories")
        print("  ✅ Locations")
        print("  ✅ Vendors")
        print("  ✅ Employees")
        print("  ✅ Rooms")
        print("  ✅ Services (definitions)")
        print("  ✅ Food Items")
        print("\nDELETED:")
        print("  ❌ All transactional data")
        print("  ❌ All bookings, purchases, stock issues, etc.")
        print("\nNext steps:")
        print("  1. Refresh your browser")
        print("  2. Create purchases to add inventory stock")
        print("  3. Start creating new bookings")
        print("  4. System is ready for fresh data")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Unexpected error during cleanup: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    clear_all_transactional_data()
