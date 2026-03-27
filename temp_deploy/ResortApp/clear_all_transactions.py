"""
Clear All Transactional Data
This script removes all transaction records while preserving master data.
"""
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    print("=" * 80)
    print("CLEARING ALL TRANSACTIONAL DATA")
    print("=" * 80)
    print("\nThis will delete:")
    print("  - All bookings and reservations")
    print("  - All service requests and assignments")
    print("  - All inventory transactions (purchases, issues, transfers)")
    print("  - All food orders")
    print("  - All checkout requests and bills")
    print("  - All payments and expenses")
    print("\nMaster data will be preserved:")
    print("  - Rooms, Inventory Items, Users, Services, etc.")
    print("=" * 80)
    
    # Confirm
    response = input("\nAre you sure you want to proceed? (type 'YES' to confirm): ")
    if response != "YES":
        print("Operation cancelled.")
        db.close()
        exit()
    
    print("\nStarting cleanup...")
    
    # 1. Clear Checkout Requests & Bills FIRST (they reference bookings)
    print("\n[1/12] Clearing checkout requests and bills...")
    db.execute(text("DELETE FROM checkout_verifications"))
    db.execute(text("DELETE FROM checkout_payments"))
    db.execute(text("DELETE FROM checkout_requests"))
    db.execute(text("DELETE FROM checkouts"))
    print("  ✓ Checkout data cleared")
    
    # 2. Clear Bookings
    print("[2/12] Clearing bookings...")
    db.execute(text("DELETE FROM booking_rooms"))
    db.execute(text("DELETE FROM bookings"))
    db.execute(text("DELETE FROM package_booking_rooms"))
    db.execute(text("DELETE FROM package_bookings"))
    print("  ✓ Bookings cleared")
    
    # 3. Clear Service Assignments & Requests
    print("[3/12] Clearing service assignments and requests...")
    db.execute(text("DELETE FROM employee_inventory_assignments"))
    db.execute(text("DELETE FROM assigned_services"))
    db.execute(text("DELETE FROM service_requests"))
    print("  ✓ Services cleared")
    
    # 4. Clear Food Orders
    print("[4/12] Clearing food orders...")
    db.execute(text("DELETE FROM food_order_items"))
    db.execute(text("DELETE FROM food_orders"))
    print("  ✓ Food orders cleared")
    
    # 5. Clear Inventory Transactions
    print("[5/12] Clearing inventory transactions...")
    db.execute(text("DELETE FROM inventory_transactions"))
    print("  ✓ Inventory transactions cleared")
    
    # 6. Clear Purchase Orders
    print("[6/12] Clearing purchase orders...")
    db.execute(text("DELETE FROM purchase_details"))
    db.execute(text("DELETE FROM purchase_masters"))
    print("  ✓ Purchase orders cleared")
    
    # 7. Clear Stock Issues
    print("[7/12] Clearing stock issues...")
    db.execute(text("DELETE FROM stock_issue_details"))
    db.execute(text("DELETE FROM stock_issues"))
    print("  ✓ Stock issues cleared")
    
    # 8. Clear Stock Requisitions
    print("[8/12] Clearing stock requisitions...")
    db.execute(text("DELETE FROM stock_requisition_details"))
    db.execute(text("DELETE FROM stock_requisitions"))
    print("  ✓ Stock requisitions cleared")
    
    # 9. Clear Waste Logs
    print("[9/12] Clearing waste logs...")
    db.execute(text("DELETE FROM waste_logs"))
    print("  ✓ Waste logs cleared")
    
    # 10. Clear Payments & Expenses
    print("[10/12] Clearing payments and expenses...")
    db.execute(text("DELETE FROM payments"))
    db.execute(text("DELETE FROM expenses"))
    print("  ✓ Payments and expenses cleared")
    
    # 11. Clear Asset Registry (optional - keeps items but clears assignments)
    print("[11/12] Clearing asset registry...")
    db.execute(text("DELETE FROM asset_registry"))
    print("  ✓ Asset registry cleared")
    
    # 12. Reset Location Stock to Zero
    print("[12/12] Resetting location stock...")
    db.execute(text("UPDATE location_stocks SET quantity = 0"))
    print("  ✓ Location stock reset")
    
    # Reset Room Status
    print("\n[BONUS] Resetting room status...")
    db.execute(text("UPDATE rooms SET status = 'Available'"))
    print("  ✓ All rooms set to Available")
    
    # Commit all changes
    db.commit()
    
    print("\n" + "=" * 80)
    print("✓ ALL TRANSACTIONAL DATA CLEARED SUCCESSFULLY!")
    print("=" * 80)
    print("\nYour system is now in a clean state.")
    print("Master data (rooms, items, users, services) has been preserved.")
    print("\nYou can now:")
    print("  - Create new bookings")
    print("  - Process new orders")
    print("  - Start fresh with inventory")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    db.rollback()
    print("Changes rolled back. Database unchanged.")
finally:
    db.close()
