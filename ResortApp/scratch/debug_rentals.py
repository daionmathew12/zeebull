from app.database import SessionLocal
from app.api.booking import _fetch_inventory
from app.models.inventory import StockIssue, StockIssueDetail, InventoryItem
from datetime import date

db = SessionLocal()
try:
    room_ids = [2]
    inventory = _fetch_inventory(db, room_ids, date(2020,1,1), date(2030,1,1))
    import json
    print("Inventory Result (Categorized):")
    for item in inventory:
        print(json.dumps(item, indent=2, default=str))

finally:
    db.close()
