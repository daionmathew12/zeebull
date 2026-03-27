"""
COMPREHENSIVE DATA CLEANUP SCRIPT - AUTO VERSION
Clears ALL transactional data automatically (no confirmation needed)
"""
from app.database import SessionLocal
from sqlalchemy import text

def clear_all_transactional_data():
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("⚠️  COMPREHENSIVE DATA CLEANUP - STARTING...")
        print("=" * 70)
        
        # Order matters due to foreign key constraints!
        
        # 1. Clear Checkout-related data
        print("\n1. Clearing checkout data...")
        db.execute(text("DELETE FROM checkout_payments"))
        db.execute(text("DELETE FROM checkout_requests"))
        print("   ✅ Checkout data cleared")
        
        # 2. Clear Billing/Invoices
        print("\n2. Clearing billing data...")
        db.execute(text("DELETE FROM bill_items"))
        db.execute(text("DELETE FROM bills"))
        print("   ✅ Billing data cleared")
        
        # 3. Clear Service Requests
        print("\n3. Clearing service requests...")
        db.execute(text("DELETE FROM service_requests"))
        print("   ✅ Service requests cleared")
        
        # 4. Clear Food Orders
        print("\n4. Clearing food orders...")
        db.execute(text("DELETE FROM food_order_items"))
        db.execute(text("DELETE FROM food_orders"))
        print("   ✅ Food orders cleared")
        
        # 5. Clear Assigned Services
        print("\n5. Clearing assigned services...")
        db.execute(text("DELETE FROM employee_inventory_assignments"))
        db.execute(text("DELETE FROM assigned_services"))
        print("   ✅ Assigned services cleared")
        
        # 6. Clear Bookings
        print("\n6. Clearing bookings...")
        db.execute(text("DELETE FROM booking_rooms"))
        db.execute(text("DELETE FROM package_booking_rooms"))
        db.execute(text("DELETE FROM package_bookings"))
        db.execute(text("DELETE FROM bookings"))
        print("   ✅ Bookings cleared")
        
        # 7. Clear Asset Registry & Mappings
        print("\n7. Clearing asset registry & mappings...")
        db.execute(text("DELETE FROM asset_registry"))
        db.execute(text("DELETE FROM asset_mappings"))
        print("   ✅ Asset data cleared")
        
        # 8. Clear Waste Logs
        print("\n8. Clearing waste logs...")
        db.execute(text("DELETE FROM waste_logs"))
        print("   ✅ Waste logs cleared")
        
        # 9. Clear Stock Issues
        print("\n9. Clearing stock issues...")
        db.execute(text("DELETE FROM stock_issue_details"))
        db.execute(text("DELETE FROM stock_issues"))
        print("   ✅ Stock issues cleared")
        
        # 10. Clear Stock Requisitions
        print("\n10. Clearing stock requisitions...")
        db.execute(text("DELETE FROM stock_requisition_details"))
        db.execute(text("DELETE FROM stock_requisitions"))
        print("   ✅ Stock requisitions cleared")
        
        # 11. Clear Purchases
        print("\n11. Clearing purchases...")
        db.execute(text("DELETE FROM purchase_details"))
        db.execute(text("DELETE FROM purchase_masters"))
        print("   ✅ Purchases cleared")
        
        # 12. Clear Inventory Transactions
        print("\n12. Clearing inventory transactions...")
        db.execute(text("DELETE FROM inventory_transactions"))
        print("   ✅ Inventory transactions cleared")
        
        # 13. Clear Location Stocks
        print("\n13. Clearing location stocks...")
        db.execute(text("DELETE FROM location_stocks"))
        print("   ✅ Location stocks cleared")
        
        # 14. Reset Inventory Item Stocks to 0
        print("\n14. Resetting inventory item stocks to 0...")
        db.execute(text("UPDATE inventory_items SET current_stock = 0"))
        print("   ✅ Inventory stocks reset to 0")
        
        # 15. Clear Accounting/Journal Entries
        print("\n15. Clearing accounting entries...")
        db.execute(text("DELETE FROM journal_entry_lines"))
        db.execute(text("DELETE FROM journal_entries"))
        print("   ✅ Accounting entries cleared")
        
        # 16. Clear Notifications
        print("\n16. Clearing notifications...")
        db.execute(text("DELETE FROM notifications"))
        print("   ✅ Notifications cleared")
        
        # Commit all changes
        db.commit()
        
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
        print("\nDELETED:")
        print("  ❌ All transactional data")
        print("  ❌ All bookings, purchases, stock issues, etc.")
        print("\nNext steps:")
        print("  1. Create purchases to add inventory stock")
        print("  2. Start creating new bookings")
        print("  3. System is ready for fresh data")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    clear_all_transactional_data()
