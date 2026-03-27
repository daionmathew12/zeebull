import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models.inventory import InventoryItem

db = next(get_db())

item_names = ["LED TV 43-inch", "LED Bulb 9W"]
updated_count = 0

print("\n" + "="*80)
print("UPDATING FIXED ASSETS")
print("="*80 + "\n")

for name in item_names:
    item = db.query(InventoryItem).filter(InventoryItem.name == name).first()
    if item:
        print(f"Updating '{item.name}'...")
        print(f"  - Old status: {getattr(item, 'is_asset_fixed', False)}")
        
        item.is_asset_fixed = True
        db.add(item)
        print(f"  - New status: {item.is_asset_fixed}")
        updated_count += 1
    else:
        print(f"❌ Item '{name}' not found!")

if updated_count > 0:
    db.commit()
    print(f"\n✅ Successfully updated {updated_count} items to FIXED ASSETS.")
else:
    print("\n⚠️ No items updated.")

print("="*80)
