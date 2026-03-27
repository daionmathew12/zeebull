"""
Fix all inventory stock discrepancies caused by incorrect transfer_in counting.

This script:
1. Identifies all items with stock discrepancies
2. Recalculates correct stock from transaction history
3. Updates InventoryItem.current_stock to the correct value
"""

from app.database import SessionLocal
from app.models.inventory import InventoryItem, InventoryTransaction
from datetime import datetime

db = SessionLocal()

print("=" * 80)
print("INVENTORY STOCK FIX - Correcting transfer_in counting issue")
print("=" * 80)

# Get all inventory items
items = db.query(InventoryItem).all()

fixed_count = 0
total_discrepancy = 0.0

for item in items:
    # Calculate correct stock from transactions
    transactions = db.query(InventoryTransaction).filter(
        InventoryTransaction.item_id == item.id
    ).all()
    
    calculated_stock = 0.0
    for txn in transactions:
        if txn.transaction_type == "in":
            # Purchases, returns to warehouse
            calculated_stock += txn.quantity
        elif txn.transaction_type in ["out", "transfer_out"]:
            # Consumption, issues to rooms
            calculated_stock -= txn.quantity
        elif txn.transaction_type == "adjustment":
            # Manual adjustments (can be + or -)
            calculated_stock += txn.quantity
        # IGNORE transfer_in - it doesn't affect global warehouse stock!
    
    # Round to 2 decimal places to avoid floating point issues
    calculated_stock = round(calculated_stock, 2)
    current_stock = round(item.current_stock or 0.0, 2)
    
    discrepancy = current_stock - calculated_stock
    
    if abs(discrepancy) > 0.01:  # More than 1 cent difference
        print(f"\n📦 {item.name} (ID: {item.id})")
        print(f"   Current Stock (WRONG): {current_stock} {item.unit}")
        print(f"   Correct Stock:         {calculated_stock} {item.unit}")
        print(f"   Discrepancy:           {discrepancy} {item.unit}")
        
        # Update to correct value
        item.current_stock = calculated_stock
        fixed_count += 1
        total_discrepancy += abs(discrepancy)

if fixed_count > 0:
    print("\n" + "=" * 80)
    print(f"✓ Fixed {fixed_count} items")
    print(f"✓ Total discrepancy corrected: {round(total_discrepancy, 2)} units")
    print("=" * 80)
    
    # Commit changes
    db.commit()
    print("\n✓ Changes committed to database")
else:
    print("\n✓ No discrepancies found - all stock values are correct!")

db.close()
