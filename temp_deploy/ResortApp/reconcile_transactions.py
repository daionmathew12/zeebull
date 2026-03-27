#!/usr/bin/env python3
"""
Add missing consumption transactions to match current stock with transaction history.
This accounts for items that were consumed but not properly recorded.
"""

from app.database import SessionLocal
from app.models.inventory import InventoryItem, InventoryTransaction
from datetime import datetime

db = SessionLocal()

print("🔧 Adding missing consumption transactions...")
print("=" * 60)

# Get all items
items = db.query(InventoryItem).all()

for item in items:
    # Calculate what the stock SHOULD be based on transactions
    in_qty = db.query(InventoryTransaction).filter(
        InventoryTransaction.item_id == item.id,
        InventoryTransaction.transaction_type.in_(['in', 'purchase'])
    ).with_entities(InventoryTransaction.quantity).all()
    
    out_qty = db.query(InventoryTransaction).filter(
        InventoryTransaction.item_id == item.id,
        InventoryTransaction.transaction_type.in_(['out', 'waste'])
    ).with_entities(InventoryTransaction.quantity).all()
    
    total_in = sum([q[0] for q in in_qty]) if in_qty else 0
    total_out = sum([q[0] for q in out_qty]) if out_qty else 0
    
    calculated_stock = total_in - total_out
    actual_stock = item.current_stock
    
    difference = calculated_stock - actual_stock
    
    if difference > 0:
        # Missing consumption transaction
        print(f"\n📦 {item.name}")
        print(f"   Calculated: {calculated_stock}, Actual: {actual_stock}")
        print(f"   Missing consumption: {difference} units")
        
        # Add consumption transaction
        txn = InventoryTransaction(
            item_id=item.id,
            transaction_type="out",
            quantity=difference,
            notes="Historical consumption - reconciliation",
            reference_number="RECON-001"
        )
        db.add(txn)
        print(f"   ✅ Added OUT transaction for {difference} units")

db.commit()
print("\n" + "=" * 60)
print("✅ Reconciliation complete!")
db.close()
