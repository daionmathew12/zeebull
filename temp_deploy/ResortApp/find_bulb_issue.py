import sys
import os
sys.path.append(os.getcwd())
from app.database import SessionLocal
from app.models.inventory import StockIssueDetail, InventoryItem, StockIssue, Location

db = SessionLocal()
item = db.query(InventoryItem).filter(InventoryItem.name == "LED Bulb 5W").first()
if not item:
    print("Bulb not found")
    sys.exit()

print(f"Bulb ID: {item.id}")

details = db.query(StockIssueDetail).filter(StockIssueDetail.item_id == item.id).all()
print(f"Found {len(details)} details for Bulb.")

for d in details:
    issue = d.issue
    loc_id = issue.destination_location_id
    loc = db.query(Location).filter(Location.id == loc_id).first()
    loc_name = loc.name if loc else "Unknown"
    print(f"Detail {d.id} | Issue {issue.issue_number} | Dest: {loc_id} ({loc_name}) | Rent: {d.rental_price}")
