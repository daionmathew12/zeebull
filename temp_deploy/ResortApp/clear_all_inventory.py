#!/usr/bin/env python3
"""
Clear all inventory transactions and reset stock to zero.
This gives you a clean slate to start fresh.
"""

from app.database import SessionLocal
from app.models.inventory import InventoryTransaction, InventoryItem, LocationStock

db = SessionLocal()

print("🧹 Clearing all inventory transactions and stock...")
print("=" * 60)

# 1. Delete all inventory transactions
txn_count = db.query(InventoryTransaction).count()
print(f"\n📋 Found {txn_count} transactions")
db.query(InventoryTransaction).delete()
print(f"✅ Deleted all {txn_count} transactions")

# 2. Reset all item stocks to 0
items = db.query(InventoryItem).all()
print(f"\n📦 Found {len(items)} items")
for item in items:
    if item.current_stock != 0:
        print(f"   {item.name}: {item.current_stock} → 0")
        item.current_stock = 0

print(f"✅ Reset all item stocks to 0")

# 3. Clear all location stocks
loc_stock_count = db.query(LocationStock).count()
print(f"\n📍 Found {loc_stock_count} location stock entries")
db.query(LocationStock).delete()
print(f"✅ Deleted all location stocks")

db.commit()

print("\n" + "=" * 60)
print("✅ All transactions and stock cleared!")
print("\n📝 Next steps:")
print("   1. Create new purchase orders to add stock")
print("   2. Receive items into warehouse")
print("   3. Issue items to rooms as needed")
print("\n🎉 You now have a clean slate!")

db.close()
