"""
STOCK CALCULATION FIX

The issue: transfer_in transactions are being counted in global stock calculations,
causing the stock to appear higher than it actually is.

Current behavior:
- Stock Issue (Warehouse → Room):
  - Creates transfer_out (decreases global stock) ✓
  - Creates transfer_in (incorrectly increases global stock) ✗
  - Net effect: No change to global stock (WRONG!)

Correct behavior:
- Stock Issue (Warehouse → Room):
  - Decreases InventoryItem.current_stock (global/warehouse)
  - Increases LocationStock.quantity (room)
  - Creates transfer_out transaction (for audit trail)
  - Creates transfer_in transaction (for audit trail ONLY, should NOT affect global stock)

Solution:
When calculating stock from transaction history for GLOBAL stock (InventoryItem.current_stock),
we should:
- Count "in" transactions as +
- Count "out" transactions as -
- Count "transfer_out" transactions as -
- IGNORE "transfer_in" transactions (they only affect LocationStock, not global stock)

The transfer_in/transfer_out pair tracks the MOVEMENT of stock between locations,
but only transfer_out should affect global warehouse stock.
"""

from app.database import SessionLocal
from app.models.inventory import InventoryItem, InventoryTransaction
from sqlalchemy import func

db = SessionLocal()

# Get Mineral Water item
item = db.query(InventoryItem).filter(InventoryItem.name.like('%Mineral Water 1L%')).first()

print(f"Item: {item.name}")
print(f"Current Stock (database): {item.current_stock}")

# Calculate stock from transactions (CORRECT method)
transactions = db.query(InventoryTransaction).filter(
    InventoryTransaction.item_id == item.id
).all()

calculated_stock = 0.0
for txn in transactions:
    if txn.transaction_type == "in":
        calculated_stock += txn.quantity
    elif txn.transaction_type in ["out", "transfer_out"]:
        calculated_stock -= txn.quantity
    # IGNORE transfer_in - it doesn't affect global stock!
    
print(f"Calculated Stock (from transactions, excluding transfer_in): {calculated_stock}")
print(f"\nDiscrepancy: {item.current_stock - calculated_stock}")

if abs(item.current_stock - calculated_stock) > 0.01:
    print("\n⚠️  STOCK MISMATCH DETECTED!")
    print("This is because transfer_in transactions are being incorrectly counted.")
    print("\nRecommendation: Update frontend stock calculation to exclude transfer_in from global stock.")
else:
    print("\n✓ Stock is correct!")

db.close()
