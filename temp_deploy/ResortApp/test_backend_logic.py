from app.database import SessionLocal
from app.api.inventory import get_location_items
from app.models.user import User

db = SessionLocal()
# Get real user
user = db.query(User).first()

# I need to create a dummy 'StockIssue' for Walkie Talkie first, because it doesn't exist in DB!
# Otherwise get_location_items won't return it to checking its type.

from app.curd.inventory import create_stock_issue
from app.models.inventory import InventoryItem, Location
from datetime import datetime

# 1. Get Walkie Talkie
item = db.query(InventoryItem).filter(InventoryItem.name.ilike("%Walkie%")).first()
if not item:
    print("Walkie Talkie not found!")
    exit()

# 2. Issue it to Room 102 (ID 19)
issue_data = {
    "issue_date": datetime.now(),
    "destination_location_id": 19,
    "details": [
        {
            "item_id": item.id,
            "issued_quantity": 1,
            "unit": "pcs",
            "is_payable": True,
            "notes": "Test Backend Logic"
        }
    ]
}

print("Creating dummy issue for Walkie Talkie...")
try:
    create_stock_issue(db, issue_data, issued_by=1)
except Exception as e:
    print(f"Error creating issue: {e}") 
    # It might fail on stock check (warning), but create anyway?
    # No, create_stock_issue commits? Yes.

# 3. Call get_location_items
print("Calling get_location_items...")
response = get_location_items(19, db, user)
# response is a dict or valid JSON structure

items = response["items"]
found = False
for i in items:
    if "Walkie" in i["item_name"]:
        print("FOUND WALKIE TALKIE!")
        print(f"  Type: {i['type']}") # This is what we want to verify!
        found = True

if not found:
    print("Walkie Talkie still not found in response items.")

db.close()
