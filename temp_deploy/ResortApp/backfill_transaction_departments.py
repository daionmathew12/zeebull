"""
Backfill department field for existing inventory transactions
"""
from app.database import SessionLocal
from app.models.inventory import InventoryTransaction, InventoryItem
from sqlalchemy import func

db = SessionLocal()

print("=" * 60)
print("BACKFILLING DEPARTMENT FOR EXISTING TRANSACTIONS")
print("=" * 60)

# Get all transactions with NULL department
null_dept_transactions = db.query(InventoryTransaction).filter(
    InventoryTransaction.department.is_(None)
).all()

print(f"\nFound {len(null_dept_transactions)} transactions with NULL department")

updated_count = 0
skipped_count = 0

for txn in null_dept_transactions:
    # Get the item
    item = db.query(InventoryItem).filter(InventoryItem.id == txn.item_id).first()
    
    if item and item.category and item.category.parent_department:
        # Update the transaction with the department
        txn.department = item.category.parent_department
        updated_count += 1
        print(f"  ✓ Updated {txn.reference_number}: {item.name} → {txn.department}")
    else:
        # Set a default based on transaction type
        if txn.reference_number and txn.reference_number.startswith("ORD-"):
            txn.department = "Restaurant"
            updated_count += 1
            print(f"  ✓ Updated {txn.reference_number}: Food Order → Restaurant")
        elif txn.reference_number and txn.reference_number.startswith("SVC-"):
            txn.department = "Housekeeping"
            updated_count += 1
            print(f"  ✓ Updated {txn.reference_number}: Service → Housekeeping")
        else:
            skipped_count += 1
            print(f"  ⚠ Skipped {txn.reference_number}: No category/department info")

# Commit changes
db.commit()

print(f"\n{'=' * 60}")
print(f"SUMMARY:")
print(f"  Updated: {updated_count}")
print(f"  Skipped: {skipped_count}")
print(f"{'=' * 60}")

# Show new department summary
print(f"\nNEW DEPARTMENT-WISE SUMMARY:")
print("-" * 60)

dept_stats = db.query(
    InventoryTransaction.department,
    func.count(InventoryTransaction.id).label('count'),
    func.sum(InventoryTransaction.total_amount).label('total')
).filter(
    InventoryTransaction.transaction_type == 'out'
).group_by(InventoryTransaction.department).all()

for dept, count, total in dept_stats:
    dept_name = dept or "Uncategorized"
    amount = total or 0
    print(f"  {dept_name:20s} | {count:3d} transactions | ₹{amount:,.2f}")

db.close()
print("\n✅ Backfill complete!")
