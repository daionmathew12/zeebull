import sys
import os
sys.path.append(os.getcwd())
from app.database import SessionLocal
from app.models.inventory import StockIssueDetail, InventoryItem

db = SessionLocal()

item_names = ["LED Bulb 5W", "Extension Cord", "Bed Sheet (King)", "Tube Light 20W", "A4 Paper Ream", "Smart TV 43-inch"]

# Find IDs
target_item_ids = [item.id for item in db.query(InventoryItem).filter(InventoryItem.name.in_(item_names)).all()]

if not target_item_ids:
    print("No items found matching the names.")
    sys.exit()

print(f"Target Item IDs: {target_item_ids}")

# Find details with rental_price > 0 for these items
details = db.query(StockIssueDetail).filter(
    StockIssueDetail.item_id.in_(target_item_ids),
    StockIssueDetail.rental_price > 0
).all()

print(f"Found {len(details)} invalid rental entries.")

for detail in details:
    print(f"Fixing Issue Detail ID {detail.id}: Item {detail.item_id}, Rental Price {detail.rental_price} -> 0.0")
    detail.rental_price = 0.0

db.commit()
print("Rental prices fixed.")
