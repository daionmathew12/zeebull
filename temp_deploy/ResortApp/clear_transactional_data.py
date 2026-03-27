#!/usr/bin/env python3
"""
Clear Transactional Data Script

This script clears all transactional data including:
- Purchases
- Stock Issues
- Inventory Transactions
- Location Stocks
- Bookings
- Checkouts
- Service Requests
- Food Orders

Master data is preserved:
- Users
- Inventory Items
- Categories
- Locations
- Vendors
- Employees
- Rooms
- Services

Usage:
    python clear_transactional_data.py --confirm
"""

import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database import SQLALCHEMY_DATABASE_URL


def clear_transactional_data(session, dry_run=True):
    """
    Clear all transactional data while preserving master data
    """
    print("\n" + "="*80)
    print("CLEARING TRANSACTIONAL DATA" + (" (DRY RUN)" if dry_run else " (EXECUTING)"))
    print("="*80 + "\n")
    
    # List of tables to clear (in order to respect foreign keys)
    tables_to_clear = [
        # Checkout related
        ("checkout_verifications", "Checkout Verifications"),
        ("checkout_payments", "Checkout Payments"),
        ("checkout_requests", "Checkout Requests"),
        ("checkouts", "Checkouts"),
        
        # Service related
        ("service_requests", "Service Requests"),
        ("service_assignments", "Service Assignments"),
        
        # Food related
        ("food_order_items", "Food Order Items"),
        ("food_orders", "Food Orders"),
        
        # Booking related
        ("package_booking_rooms", "Package Booking Rooms"),
        ("package_bookings", "Package Bookings"),
        ("booking_rooms", "Booking Rooms"),
        ("bookings", "Bookings"),
        
        # Inventory transactions
        ("waste_logs", "Waste Logs"),
        ("stock_issue_details", "Stock Issue Details"),
        ("stock_issues", "Stock Issues"),
        ("stock_requisition_details", "Stock Requisition Details"),
        ("stock_requisitions", "Stock Requisitions"),
        ("purchase_details", "Purchase Details"),
        ("purchase_masters", "Purchase Masters"),
        ("inventory_transactions", "Inventory Transactions"),
        ("location_stocks", "Location Stocks"),
        
        # Asset tracking
        ("asset_registry", "Asset Registry"),
        ("asset_mappings", "Asset Mappings"),
        
        # Billing
        ("billing_records", "Billing Records"),
        
        # Payments
        ("payments", "Payments"),
        
        # Expenses
        ("expenses", "Expenses"),
    ]
    
    total_deleted = 0
    results = []
    
    for table_name, description in tables_to_clear:
        try:
            # Check if table exists
            check_query = text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = '{table_name}'
                )
            """)
            exists = session.execute(check_query).scalar()
            
            if not exists:
                print(f"⚠️  Table '{table_name}' does not exist, skipping...")
                continue
            
            # Count records
            count_query = text(f"SELECT COUNT(*) FROM {table_name}")
            count = session.execute(count_query).scalar()
            
            if count == 0:
                print(f"✓ {description} ({table_name}): Already empty")
                results.append({
                    "table": table_name,
                    "description": description,
                    "count": 0,
                    "status": "empty"
                })
                continue
            
            # Delete records
            if not dry_run:
                delete_query = text(f"DELETE FROM {table_name}")
                session.execute(delete_query)
                print(f"✓ {description} ({table_name}): Deleted {count} records")
                total_deleted += count
                results.append({
                    "table": table_name,
                    "description": description,
                    "count": count,
                    "status": "deleted"
                })
            else:
                print(f"  {description} ({table_name}): Would delete {count} records")
                total_deleted += count
                results.append({
                    "table": table_name,
                    "description": description,
                    "count": count,
                    "status": "would_delete"
                })
                
        except Exception as e:
            print(f"❌ Error processing {table_name}: {e}")
            results.append({
                "table": table_name,
                "description": description,
                "count": 0,
                "status": "error",
                "error": str(e)
            })
    
    # Reset inventory item stocks to 0
    print("\n" + "-"*80)
    print("RESETTING INVENTORY STOCKS")
    print("-"*80 + "\n")
    
    try:
        count_query = text("SELECT COUNT(*) FROM inventory_items WHERE current_stock > 0")
        items_with_stock = session.execute(count_query).scalar()
        
        if items_with_stock > 0:
            if not dry_run:
                reset_query = text("UPDATE inventory_items SET current_stock = 0")
                session.execute(reset_query)
                print(f"✓ Reset stock to 0 for {items_with_stock} inventory items")
            else:
                print(f"  Would reset stock to 0 for {items_with_stock} inventory items")
        else:
            print("✓ All inventory items already have 0 stock")
            
    except Exception as e:
        print(f"❌ Error resetting inventory stocks: {e}")
    
    # Commit if not dry run
    if not dry_run:
        session.commit()
        print("\n" + "="*80)
        print(f"✅ SUCCESSFULLY DELETED {total_deleted} RECORDS")
        print("="*80 + "\n")
    else:
        print("\n" + "="*80)
        print(f"⚠️  DRY RUN: Would delete {total_deleted} records")
        print("   Run with --confirm to actually delete")
        print("="*80 + "\n")
    
    return results, total_deleted


def verify_master_data(session):
    """
    Verify that master data is still intact
    """
    print("\n" + "="*80)
    print("VERIFYING MASTER DATA")
    print("="*80 + "\n")
    
    master_tables = [
        ("users", "Users"),
        ("inventory_items", "Inventory Items"),
        ("inventory_categories", "Inventory Categories"),
        ("locations", "Locations"),
        ("vendors", "Vendors"),
        ("employees", "Employees"),
        ("rooms", "Rooms"),
        ("services", "Services"),
        ("food_items", "Food Items"),
        ("food_categories", "Food Categories"),
    ]
    
    for table_name, description in master_tables:
        try:
            count_query = text(f"SELECT COUNT(*) FROM {table_name}")
            count = session.execute(count_query).scalar()
            print(f"✓ {description}: {count} records")
        except Exception as e:
            print(f"❌ Error checking {table_name}: {e}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Clear transactional data')
    parser.add_argument('--confirm', action='store_true', help='Actually delete data (not dry run)')
    parser.add_argument('--verify-only', action='store_true', help='Only verify master data, do not delete')
    
    args = parser.parse_args()
    
    # Create database session
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        if args.verify_only:
            verify_master_data(session)
        else:
            # Clear transactional data
            results, total = clear_transactional_data(session, dry_run=not args.confirm)
            
            # Verify master data is intact
            verify_master_data(session)
            
            # Summary
            print("\n" + "="*80)
            print("SUMMARY")
            print("="*80 + "\n")
            
            if args.confirm:
                print("✅ Transactional data cleared successfully")
                print(f"   Total records deleted: {total}")
                print("\n📝 Next steps:")
                print("   1. Verify master data is intact (shown above)")
                print("   2. Create new purchases to add stock")
                print("   3. Test the new stock management fixes")
            else:
                print("⚠️  DRY RUN COMPLETE")
                print(f"   Would delete {total} records")
                print("\n   Run with --confirm to actually delete:")
                print("   python clear_transactional_data.py --confirm")
        
        print("\n" + "="*80)
        print("COMPLETE")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        session.rollback()
    finally:
        session.close()


if __name__ == '__main__':
    main()
