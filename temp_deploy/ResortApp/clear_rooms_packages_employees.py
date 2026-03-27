"""
Script to clear all rooms, packages, employees, accounting data, and inventory from the database.
This will also clear all related data (bookings, images, leaves, attendance, expenses, journal entries, locations, stock, etc.)
"""
import sys
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.room import Room
from app.models.Package import Package, PackageImage, PackageBooking, PackageBookingRoom
from app.models.employee import Employee, Leave, Attendance, WorkingLog
from app.models.booking import Booking, BookingRoom
from app.models.user import User
from app.models.expense import Expense
from app.models.account import JournalEntryLine, JournalEntry, AccountLedger, AccountGroup
from app.models.inventory import (
    LocationStock, AssetMapping, AssetRegistry, Location,
    WasteLog, StockIssueDetail, StockIssue, StockRequisitionDetail, StockRequisition,
    InventoryTransaction, PurchaseDetail, PurchaseMaster, InventoryItem,
    Vendor, InventoryCategory
)


def clear_all_data():
    """Clear all rooms, packages, and employees from the database"""
    db: Session = SessionLocal()
    
    try:
        print("=" * 60)
        print("CLEARING ROOMS, PACKAGES, EMPLOYEES & ACCOUNTING DATA")
        print("=" * 60)
        print()
        
        # Get counts before deletion
        room_count = db.query(Room).count()
        package_count = db.query(Package).count()
        employee_count = db.query(Employee).count()
        package_booking_count = db.query(PackageBooking).count()
        booking_count = db.query(Booking).count()
        expense_count = db.query(Expense).count()
        journal_entry_count = db.query(JournalEntry).count()
        ledger_count = db.query(AccountLedger).count()
        account_group_count = db.query(AccountGroup).count()
        
        # Inventory counts
        location_count = db.query(Location).count()
        location_stock_count = db.query(LocationStock).count()
        inventory_item_count = db.query(InventoryItem).count()
        inventory_category_count = db.query(InventoryCategory).count()
        vendor_count = db.query(Vendor).count()
        purchase_count = db.query(PurchaseMaster).count()
        
        print(f"📊 Current Data:")
        print(f"\n   🏨 Rooms & Bookings:")
        print(f"      - Rooms: {room_count}")
        print(f"      - Regular Bookings: {booking_count}")
        print(f"\n   📦 Packages:")
        print(f"      - Packages: {package_count}")
        print(f"      - Package Bookings: {package_booking_count}")
        print(f"\n   👥 Employees:")
        print(f"      - Employees: {employee_count}")
        print(f"      - Expenses: {expense_count}")
        print(f"\n   💰 Accounting:")
        print(f"      - Journal Entries: {journal_entry_count}")
        print(f"      - Account Ledgers: {ledger_count}")
        print(f"      - Account Groups: {account_group_count}")
        print(f"\n   📦 Inventory:")
        print(f"      - Locations: {location_count}")
        print(f"      - Location Stock Records: {location_stock_count}")
        print(f"      - Inventory Items: {inventory_item_count}")
        print(f"      - Inventory Categories: {inventory_category_count}")
        print(f"      - Vendors: {vendor_count}")
        print(f"      - Purchases: {purchase_count}")
        print()
        
        total_items = (room_count + package_count + employee_count + 
                      expense_count + journal_entry_count + ledger_count + account_group_count +
                      location_count + location_stock_count + inventory_item_count + 
                      inventory_category_count + vendor_count + purchase_count)
        
        if total_items == 0:
            print("✅ Database is already clean. Nothing to delete.")
            return
        
        # Confirm deletion
        print("⚠️  WARNING: This will delete ALL data from the database!")
        print("   This includes:")
        print("   - All rooms and their bookings")
        print("   - All packages, package images, and package bookings")
        print("   - All employees, their leaves, attendance, working logs, and expenses")
        print("   - All accounting data (journal entries, ledgers, account groups)")
        print("   - All inventory data (locations, stock, items, categories, vendors, purchases)")
        print("   - Associated user accounts for employees")
        print()
        
        response = input("Are you sure you want to continue? (yes/no): ").strip().lower()
        
        if response != "yes":
            print("❌ Operation cancelled.")
            return
        
        print()
        print("🗑️  Starting deletion process...")
        print()
        
        # 1. Delete Accounting Data (must be done first due to foreign key constraints)
        print("1️⃣  Deleting accounting data...")
        deleted_journal_lines = db.query(JournalEntryLine).delete()
        print(f"   ✓ Deleted {deleted_journal_lines} journal entry lines")
        
        deleted_journal_entries = db.query(JournalEntry).delete()
        print(f"   ✓ Deleted {deleted_journal_entries} journal entries")
        
        deleted_ledgers = db.query(AccountLedger).delete()
        print(f"   ✓ Deleted {deleted_ledgers} account ledgers")
        
        deleted_account_groups = db.query(AccountGroup).delete()
        print(f"   ✓ Deleted {deleted_account_groups} account groups")
        print()
        
        # 2. Delete Package-related data
        print("2️⃣  Deleting package bookings and related data...")
        deleted_package_booking_rooms = db.query(PackageBookingRoom).delete()
        print(f"   ✓ Deleted {deleted_package_booking_rooms} package booking rooms")
        
        deleted_package_bookings = db.query(PackageBooking).delete()
        print(f"   ✓ Deleted {deleted_package_bookings} package bookings")
        
        deleted_package_images = db.query(PackageImage).delete()
        print(f"   ✓ Deleted {deleted_package_images} package images")
        
        deleted_packages = db.query(Package).delete()
        print(f"   ✓ Deleted {deleted_packages} packages")
        print()
        
        # 3. Delete Room-related data
        print("3️⃣  Deleting room bookings and related data...")
        deleted_booking_rooms = db.query(BookingRoom).delete()
        print(f"   ✓ Deleted {deleted_booking_rooms} booking rooms")
        
        deleted_bookings = db.query(Booking).delete()
        print(f"   ✓ Deleted {deleted_bookings} bookings")
        
        deleted_rooms = db.query(Room).delete()
        print(f"   ✓ Deleted {deleted_rooms} rooms")
        print()
        
        # 4. Delete Inventory data (before employees since some may reference users)
        print("4️⃣  Deleting inventory data...")
        
        # Delete in correct order due to foreign keys
        deleted_location_stock = db.query(LocationStock).delete()
        print(f"   ✓ Deleted {deleted_location_stock} location stock records")
        
        deleted_asset_mappings = db.query(AssetMapping).delete()
        print(f"   ✓ Deleted {deleted_asset_mappings} asset mappings")
        
        deleted_asset_registry = db.query(AssetRegistry).delete()
        print(f"   ✓ Deleted {deleted_asset_registry} asset registry entries")
        
        deleted_waste_logs = db.query(WasteLog).delete()
        print(f"   ✓ Deleted {deleted_waste_logs} waste logs")
        
        deleted_stock_issue_details = db.query(StockIssueDetail).delete()
        print(f"   ✓ Deleted {deleted_stock_issue_details} stock issue details")
        
        deleted_stock_issues = db.query(StockIssue).delete()
        print(f"   ✓ Deleted {deleted_stock_issues} stock issues")
        
        deleted_stock_req_details = db.query(StockRequisitionDetail).delete()
        print(f"   ✓ Deleted {deleted_stock_req_details} stock requisition details")
        
        deleted_stock_reqs = db.query(StockRequisition).delete()
        print(f"   ✓ Deleted {deleted_stock_reqs} stock requisitions")
        
        deleted_inv_transactions = db.query(InventoryTransaction).delete()
        print(f"   ✓ Deleted {deleted_inv_transactions} inventory transactions")
        
        deleted_purchase_details = db.query(PurchaseDetail).delete()
        print(f"   ✓ Deleted {deleted_purchase_details} purchase details")
        
        deleted_purchases = db.query(PurchaseMaster).delete()
        print(f"   ✓ Deleted {deleted_purchases} purchases")
        
        deleted_locations = db.query(Location).delete()
        print(f"   ✓ Deleted {deleted_locations} locations")
        
        deleted_items = db.query(InventoryItem).delete()
        print(f"   ✓ Deleted {deleted_items} inventory items")
        
        deleted_vendors = db.query(Vendor).delete()
        print(f"   ✓ Deleted {deleted_vendors} vendors")
        
        deleted_categories = db.query(InventoryCategory).delete()
        print(f"   ✓ Deleted {deleted_categories} inventory categories")
        print()
        
        # 5. Delete Employee-related data
        print("5️⃣  Deleting employee data...")
        
        # Delete expenses first
        deleted_expenses = db.query(Expense).delete()
        print(f"   ✓ Deleted {deleted_expenses} expenses")
        
        deleted_working_logs = db.query(WorkingLog).delete()
        print(f"   ✓ Deleted {deleted_working_logs} working logs")
        
        deleted_attendance = db.query(Attendance).delete()
        print(f"   ✓ Deleted {deleted_attendance} attendance records")
        
        deleted_leaves = db.query(Leave).delete()
        print(f"   ✓ Deleted {deleted_leaves} leave records")
        
        # Get employee user IDs before deleting employees
        employee_user_ids = [emp.user_id for emp in db.query(Employee).all() if emp.user_id]
        
        deleted_employees = db.query(Employee).delete()
        print(f"   ✓ Deleted {deleted_employees} employees")
        
        # Delete associated user accounts
        if employee_user_ids:
            deleted_users = db.query(User).filter(User.id.in_(employee_user_ids)).delete(synchronize_session=False)
            print(f"   ✓ Deleted {deleted_users} employee user accounts")
        print()
        
        # Commit all changes
        db.commit()
        
        print("=" * 60)
        print("✅ SUCCESS! All data has been cleared.")
        print("=" * 60)
        print()
        print("📊 Summary:")
        print(f"   - Deleted {deleted_rooms} rooms")
        print(f"   - Deleted {deleted_packages} packages")
        print(f"   - Deleted {deleted_employees} employees")
        print(f"   - Deleted {deleted_bookings + deleted_package_bookings} total bookings")
        print(f"   - Deleted {deleted_expenses} expenses")
        print(f"   - Deleted {deleted_journal_entries} journal entries")
        print(f"   - Deleted {deleted_ledgers} account ledgers")
        print(f"   - Deleted {deleted_account_groups} account groups")
        print(f"   - Deleted {deleted_locations} locations")
        print(f"   - Deleted {deleted_location_stock} location stock records")
        print(f"   - Deleted {deleted_items} inventory items")
        print(f"   - Deleted {deleted_categories} inventory categories")
        print(f"   - Deleted {deleted_vendors} vendors")
        print(f"   - Deleted {deleted_purchases} purchases")
        print()
        
    except Exception as e:
        db.rollback()
        print()
        print("=" * 60)
        print("❌ ERROR occurred during deletion!")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print()
        print("Database has been rolled back. No changes were made.")
        sys.exit(1)
        
    finally:
        db.close()


if __name__ == "__main__":
    clear_all_data()
