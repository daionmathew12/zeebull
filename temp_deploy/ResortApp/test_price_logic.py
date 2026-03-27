from app.database import SessionLocal
from app.curd.inventory import create_stock_issue
from app.models.inventory import InventoryItem, Location, StockIssue
from datetime import datetime

db = SessionLocal()

# 1. Get Coca Cola Item
item = db.query(InventoryItem).filter(InventoryItem.name.ilike("%Coca%")).first()
if not item:
    print("Coca Cola not found!")
    exit()

print(f"Testing Item: {item.name}")
print(f"  Cost: {item.unit_price}")
print(f"  Selling: {item.selling_price}")

# 2. Prepare Issue Data
issue_data = {
    "issue_date": datetime.now(),
    "details": [
        {
            "item_id": item.id,
            "issued_quantity": 1,
            "unit": "pcs",
            "is_payable": True,
            "notes": "Test Price Logic"
        }
    ]
}

# 3. creating the issue
# We need valid location IDs.
loc_room = db.query(Location).filter(Location.location_type == "GUEST_ROOM").first()
loc_wh = db.query(Location).filter(Location.location_type == "WAREHOUSE").first()

if loc_room:
    issue_data["destination_location_id"] = loc_room.id
if loc_wh:
    issue_data["source_location_id"] = loc_wh.id

try:
    print("Creating Stock Issue...")
    issue = create_stock_issue(db, issue_data, issued_by=1)
    
    # 4. Check the RESULTING detail
    detail = issue.details[0]
    print(f"RESULT Unit Price: {detail.unit_price}")
    
    if detail.unit_price == item.selling_price:
        print("SUCCESS: Used Selling Price!")
    elif detail.unit_price == item.unit_price:
        print("FAILURE: Used Cost Price!")
    else:
        print("FAILURE: Used Unknown Price!")

except Exception as e:
    print(f"Error: {e}")

db.close()
