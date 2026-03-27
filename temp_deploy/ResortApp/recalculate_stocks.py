#!/usr/bin/env python3
"""
Recalculate inventory item stocks based on transactions.
This fixes the stock discrepancy caused by incorrectly deducting stock during transfers.
"""

from app.database import SessionLocal
from app.models.inventory import InventoryItem, InventoryTransaction, LocationStock
from sqlalchemy import func

db = SessionLocal()

print("🔧 Recalculating inventory stocks...")
print("=" * 60)

# Get all items
items = db.query(InventoryItem).all()

for item in items:
    # Calculate stock from transactions
    # IN transactions: purchase, transfer_in, adjustment_in
    # OUT transactions: out (consumption), waste, adjustment_out
    # IGNORE: transfer_out (doesn't reduce global stock, just moves between locations)
    
    in_types = ['in', 'purchase', 'transfer_in', 'adjustment_in']
    out_types = ['out', 'waste', 'adjustment_out']
    
    total_in = db.query(func.sum(InventoryTransaction.quantity)).filter(
        InventoryTransaction.item_id == item.id,
        InventoryTransaction.transaction_type.in_(in_types)
    ).scalar() or 0
    
    total_out = db.query(func.sum(InventoryTransaction.quantity)).filter(
        InventoryTransaction.item_id == item.id,
        InventoryTransaction.transaction_type.in_(out_types)
    ).scalar() or 0
    
    calculated_stock = total_in - total_out
    
    # Also calculate from location stocks (should match)
    location_total = db.query(func.sum(LocationStock.quantity)).filter(
        LocationStock.item_id == item.id
    ).scalar() or 0
    
    old_stock = item.current_stock
    
    # Use location total as the source of truth (more accurate)
    new_stock = location_total
    
    if old_stock != new_stock:
        print(f"\n📦 {item.name}")
        print(f"   Old: {old_stock} | New: {new_stock} | Locations: {location_total}")
        print(f"   Transactions: IN={total_in}, OUT={total_out}, Calc={calculated_stock}")
        
        item.current_stock = new_stock
        print(f"   ✅ Updated to {new_stock}")

db.commit()
print("\n" + "=" * 60)
print("✅ Stock recalculation complete!")
db.close()
