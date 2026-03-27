"""
Test script to verify department tracking is working for new inventory transactions
"""
from app.database import SessionLocal
from app.models.inventory import InventoryTransaction, InventoryItem
from sqlalchemy import func

db = SessionLocal()

print("=" * 60)
print("INVENTORY TRANSACTION DEPARTMENT TRACKING TEST")
print("=" * 60)

# Check recent transactions
recent_transactions = db.query(InventoryTransaction).filter(
    InventoryTransaction.transaction_type == "out"
).order_by(InventoryTransaction.created_at.desc()).limit(10).all()

print(f"\nLast 10 'out' transactions:")
print("-" * 60)
for txn in recent_transactions:
    item = db.query(InventoryItem).filter(InventoryItem.id == txn.item_id).first()
    item_name = item.name if item else "Unknown"
    dept = txn.department or "NULL"
    amount = f"₹{txn.total_amount:.2f}" if txn.total_amount else "₹0.00"
    print(f"  {txn.reference_number:20s} | {item_name:30s} | Dept: {dept:15s} | {amount}")

# Department summary
print(f"\n{'=' * 60}")
print("DEPARTMENT-WISE INVENTORY CONSUMPTION SUMMARY")
print("=" * 60)

dept_stats = db.query(
    InventoryTransaction.department,
    func.count(InventoryTransaction.id).label('count'),
    func.sum(InventoryTransaction.total_amount).label('total')
).filter(
    InventoryTransaction.transaction_type == 'out'
).group_by(InventoryTransaction.department).all()

total_consumption = 0
for dept, count, total in dept_stats:
    dept_name = dept or "Uncategorized"
    amount = total or 0
    total_consumption += amount
    print(f"  {dept_name:20s} | {count:3d} transactions | ₹{amount:,.2f}")

print("-" * 60)
print(f"  {'TOTAL':20s} | {sum(d[1] for d in dept_stats):3d} transactions | ₹{total_consumption:,.2f}")
print("=" * 60)

# Check if any items have categories with parent_department
print("\nSample items with department info:")
print("-" * 60)
items_with_cats = db.query(InventoryItem).limit(5).all()
for item in items_with_cats:
    dept = item.category.parent_department if item.category else "No Category"
    print(f"  {item.name:40s} | Dept: {dept}")

db.close()
