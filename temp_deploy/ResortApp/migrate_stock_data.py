#!/usr/bin/env python3
"""
Stock Data Migration and Validation Script

This script helps transition to the new stock management system by:
1. Validating current stock data
2. Identifying discrepancies
3. Providing recommendations for fixes
4. Optionally applying automatic corrections

Usage:
    python migrate_stock_data.py --check          # Check only, no changes
    python migrate_stock_data.py --fix            # Apply automatic fixes
    python migrate_stock_data.py --report         # Generate detailed report
"""

import sys
import os
import argparse
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import SQLALCHEMY_DATABASE_URL
from app.models.inventory import InventoryItem, LocationStock, InventoryTransaction
from app.models.user import User


def check_stock_discrepancies(session):
    """
    Check for discrepancies between global and location stocks
    """
    print("\n" + "="*80)
    print("STOCK DISCREPANCY CHECK")
    print("="*80 + "\n")
    
    items = session.query(InventoryItem).all()
    discrepancies = []
    
    for item in items:
        # Calculate total location stock
        location_stocks = session.query(LocationStock).filter(
            LocationStock.item_id == item.id
        ).all()
        
        total_location_stock = sum(ls.quantity for ls in location_stocks)
        global_stock = item.current_stock or 0
        
        discrepancy = global_stock - total_location_stock
        
        if abs(discrepancy) > 0.01:  # Allow for floating point errors
            discrepancies.append({
                'item': item,
                'global_stock': global_stock,
                'location_stock': total_location_stock,
                'discrepancy': discrepancy,
                'locations': location_stocks
            })
    
    print(f"Total items checked: {len(items)}")
    print(f"Discrepancies found: {len(discrepancies)}\n")
    
    if discrepancies:
        print("Items with discrepancies:")
        print("-" * 80)
        for disc in discrepancies:
            print(f"\n{disc['item'].name} (ID: {disc['item'].id})")
            print(f"  Item Code: {disc['item'].item_code}")
            print(f"  Global Stock: {disc['global_stock']}")
            print(f"  Location Stock: {disc['location_stock']}")
            print(f"  Discrepancy: {disc['discrepancy']}")
            print(f"  Locations:")
            for loc in disc['locations']:
                loc_name = loc.location.name if loc.location else f"Location {loc.location_id}"
                print(f"    - {loc_name}: {loc.quantity}")
    
    return discrepancies


def check_negative_stock(session):
    """
    Check for negative stock in any location
    """
    print("\n" + "="*80)
    print("NEGATIVE STOCK CHECK")
    print("="*80 + "\n")
    
    negative_stocks = session.query(LocationStock).filter(
        LocationStock.quantity < 0
    ).all()
    
    print(f"Negative stock entries found: {len(negative_stocks)}\n")
    
    if negative_stocks:
        print("Locations with negative stock:")
        print("-" * 80)
        for stock in negative_stocks:
            item = stock.item
            loc_name = stock.location.name if stock.location else f"Location {stock.location_id}"
            print(f"\n{item.name} at {loc_name}")
            print(f"  Item ID: {item.id}")
            print(f"  Quantity: {stock.quantity}")
            print(f"  Last Updated: {stock.last_updated}")
    
    return negative_stocks


def check_transaction_integrity(session):
    """
    Check transaction history for consistency
    """
    print("\n" + "="*80)
    print("TRANSACTION INTEGRITY CHECK")
    print("="*80 + "\n")
    
    items = session.query(InventoryItem).limit(10).all()  # Sample check
    issues = []
    
    for item in items:
        transactions = session.query(InventoryTransaction).filter(
            InventoryTransaction.item_id == item.id
        ).order_by(InventoryTransaction.created_at).all()
        
        # Calculate stock from transactions
        calculated_stock = 0.0
        for txn in transactions:
            if txn.transaction_type in ['in', 'adjustment', 'transfer_in', 'return']:
                calculated_stock += txn.quantity
            elif txn.transaction_type in ['out', 'transfer_out']:
                calculated_stock -= txn.quantity
        
        global_stock = item.current_stock or 0
        diff = abs(global_stock - calculated_stock)
        
        if diff > 0.01:
            issues.append({
                'item': item,
                'global_stock': global_stock,
                'calculated_stock': calculated_stock,
                'difference': diff,
                'transaction_count': len(transactions)
            })
    
    print(f"Items checked: {len(items)}")
    print(f"Integrity issues found: {len(issues)}\n")
    
    if issues:
        print("Items with transaction integrity issues:")
        print("-" * 80)
        for issue in issues:
            print(f"\n{issue['item'].name} (ID: {issue['item'].id})")
            print(f"  Global Stock: {issue['global_stock']}")
            print(f"  Calculated from Transactions: {issue['calculated_stock']}")
            print(f"  Difference: {issue['difference']}")
            print(f"  Transaction Count: {issue['transaction_count']}")
    
    return issues


def fix_discrepancies(session, discrepancies, dry_run=True):
    """
    Fix stock discrepancies by adjusting global stock to match location stocks
    """
    print("\n" + "="*80)
    print("FIXING DISCREPANCIES" + (" (DRY RUN)" if dry_run else ""))
    print("="*80 + "\n")
    
    if not discrepancies:
        print("No discrepancies to fix!")
        return
    
    # Get system user for transactions
    system_user = session.query(User).first()
    if not system_user:
        print("ERROR: No user found in database. Cannot create transactions.")
        return
    
    fixed_count = 0
    
    for disc in discrepancies:
        item = disc['item']
        old_stock = disc['global_stock']
        new_stock = disc['location_stock']
        
        print(f"\nFixing {item.name}:")
        print(f"  Old Global Stock: {old_stock}")
        print(f"  New Global Stock: {new_stock}")
        print(f"  Adjustment: {new_stock - old_stock}")
        
        if not dry_run:
            # Update global stock
            item.current_stock = new_stock
            
            # Create adjustment transaction
            adjustment = InventoryTransaction(
                item_id=item.id,
                transaction_type='adjustment',
                quantity=abs(new_stock - old_stock),
                unit_price=item.unit_price,
                total_amount=abs(new_stock - old_stock) * (item.unit_price or 0),
                reference_number=f"MIGRATE-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                notes=f"Stock migration adjustment: {old_stock} → {new_stock}",
                created_by=system_user.id
            )
            session.add(adjustment)
            fixed_count += 1
    
    if not dry_run:
        session.commit()
        print(f"\n✅ Fixed {fixed_count} discrepancies")
    else:
        print(f"\n⚠️  DRY RUN: Would fix {len(discrepancies)} discrepancies")
        print("   Run with --fix to apply changes")


def generate_report(session):
    """
    Generate comprehensive stock report
    """
    print("\n" + "="*80)
    print("COMPREHENSIVE STOCK REPORT")
    print("="*80 + "\n")
    
    # Summary statistics
    total_items = session.query(InventoryItem).count()
    total_locations = session.query(LocationStock).count()
    total_transactions = session.query(InventoryTransaction).count()
    
    print("SUMMARY STATISTICS")
    print("-" * 80)
    print(f"Total Inventory Items: {total_items}")
    print(f"Total Location Stock Entries: {total_locations}")
    print(f"Total Transactions: {total_transactions}")
    
    # Stock by location type
    print("\n\nSTOCK BY LOCATION TYPE")
    print("-" * 80)
    from app.models.inventory import Location
    from sqlalchemy import func
    
    location_summary = session.query(
        Location.location_type,
        func.count(LocationStock.id).label('item_count'),
        func.sum(LocationStock.quantity).label('total_quantity')
    ).join(LocationStock).group_by(Location.location_type).all()
    
    for loc_type, item_count, total_qty in location_summary:
        print(f"{loc_type}: {item_count} items, {total_qty} total quantity")
    
    # Recent transactions
    print("\n\nRECENT TRANSACTIONS (Last 10)")
    print("-" * 80)
    recent_txns = session.query(InventoryTransaction).order_by(
        InventoryTransaction.created_at.desc()
    ).limit(10).all()
    
    for txn in recent_txns:
        item = session.query(InventoryItem).filter(InventoryItem.id == txn.item_id).first()
        item_name = item.name if item else f"Item {txn.item_id}"
        print(f"{txn.created_at.strftime('%Y-%m-%d %H:%M')} | {txn.transaction_type:15} | {item_name:30} | Qty: {txn.quantity}")


def main():
    parser = argparse.ArgumentParser(description='Stock Data Migration and Validation')
    parser.add_argument('--check', action='store_true', help='Check for discrepancies only')
    parser.add_argument('--fix', action='store_true', help='Fix discrepancies automatically')
    parser.add_argument('--report', action='store_true', help='Generate detailed report')
    
    args = parser.parse_args()
    
    # If no arguments, show help
    if not (args.check or args.fix or args.report):
        parser.print_help()
        return
    
    # Create database session
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        if args.report:
            generate_report(session)
        
        if args.check or args.fix:
            # Run checks
            discrepancies = check_stock_discrepancies(session)
            negative_stocks = check_negative_stock(session)
            transaction_issues = check_transaction_integrity(session)
            
            if args.fix:
                # Apply fixes
                fix_discrepancies(session, discrepancies, dry_run=False)
            else:
                # Dry run
                fix_discrepancies(session, discrepancies, dry_run=True)
        
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
