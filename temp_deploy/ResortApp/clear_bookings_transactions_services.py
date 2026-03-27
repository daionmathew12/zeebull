"""
Clear all bookings, transactions, and services data
WARNING: This will delete all booking, service, and transaction records!
"""
from app.database import SessionLocal
from sqlalchemy import text


def clear_all_data():
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("⚠️  CLEAR ALL BOOKINGS, TRANSACTIONS & SERVICES")
        print("=" * 70)
        print()
        print("This will DELETE:")
        print("  - All bookings and related data")
        print("  - All services and assignments")
        print("  - All inventory transactions")
        print("  - All checkout data")
        print("  - All food orders")
        print()
        print("⚠️  WARNING: This action CANNOT be undone!")
        print()
        
        # Count records using raw SQL to avoid model dependencies
        tables_to_clear = [
            "checkout_payments",
            "checkout_requests",
            "checkouts",
            "service_requests",
            "assigned_services",
            "food_orders",
            "booking_rooms",
            "bookings",
            "package_booking_rooms",
            "package_bookings",
            "inventory_transactions"
        ]
        
        total_records = 0
        table_counts = {}
        
        for table in tables_to_clear:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                table_counts[table] = count
                total_records += count
            except Exception as e:
                print(f"⚠️  Could not count {table}: {e}")
                table_counts[table] = 0
        
        print(f"Records to be deleted:")
        for table, count in table_counts.items():
            print(f"  - {table}: {count}")
        print(f"  TOTAL: {total_records} records")
        print()
        
        if total_records == 0:
            print("✅ No records to delete. Database is already clean.")
            return
        
        confirm1 = input("Type 'DELETE ALL' to confirm: ").strip()
        
        if confirm1 != "DELETE ALL":
            print("❌ Operation cancelled")
            return
        
        print()
        confirm2 = input("Are you absolutely sure? (yes/no): ").strip().lower()
        
        if confirm2 != "yes":
            print("❌ Operation cancelled")
            return
        
        print()
        print("=" * 70)
        print("DELETING RECORDS...")
        print("=" * 70)
        print()
        
        # Delete in correct order to avoid foreign key constraints
        deletion_order = [
            "checkout_payments",
            "checkout_requests",
            "checkouts",
            "service_requests",
            "assigned_services",
            "food_orders",
            "booking_rooms",
            "bookings",
            "package_booking_rooms",
            "package_bookings",
            "inventory_transactions"
        ]
        
        for table in deletion_order:
            try:
                result = db.execute(text(f"DELETE FROM {table}"))
                deleted = result.rowcount
                print(f"✅ Deleted {deleted} records from {table}")
            except Exception as e:
                print(f"⚠️  Error deleting from {table}: {e}")
        
        db.commit()
        
        print()
        print("=" * 70)
        print("✅ ALL DATA CLEARED SUCCESSFULLY!")
        print("=" * 70)
        print()
        print(f"Total records deleted: {total_records}")
        print()
        print("⚠️  NOTE: Inventory stock levels have NOT been reset.")
        print("   You may need to manually adjust inventory if needed.")
        print()
        
    except Exception as e:
        db.rollback()
        print()
        print("=" * 70)
        print("❌ ERROR")
        print("=" * 70)
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


if __name__ == "__main__":
    clear_all_data()
