
import os
import sys
# Add the current directory to sys.path
sys.path.append(os.getcwd())

from app.utils.auth import get_db
from app.models.inventory import LaundryLog, InventoryTransaction, Location, InventoryItem
from sqlalchemy import desc

db = next(get_db())

print("--- RECENT LAUNDRY LOGS ---")
logs = db.query(LaundryLog).order_by(desc(LaundryLog.id)).limit(10).all()
for l in logs:
    print(f"ID: {l.id}, Item Order: {l.item_id}, Qty: {l.quantity}, Status: {l.status}, Branch: {l.branch_id}, Room: {l.room_number}")

print("\n--- NEW LAUNDRY TRANSACTIONS (Type: laundry) ---")
lnd_txns = db.query(InventoryTransaction).filter(InventoryTransaction.transaction_type == "laundry").all()
for t in lnd_txns:
    print(f"ID: {t.id}, Item: {t.item_id}, Type: {t.transaction_type}, Qty: {t.quantity}, Branch: {t.branch_id}, Ref: {t.reference_number}")

print("\n--- WASTE LOGS ---")
from app.models.inventory import WasteLog
waste = db.query(WasteLog).order_by(WasteLog.id.desc()).limit(5).all()
for w in waste:
    print(f"ID: {w.id}, Item: {w.item_id}, Qty: {w.quantity}, Reason: {w.reason_code}, Branch: {w.branch_id}")

print("\n--- LATEST LAUNDRY LOGS ---")
lLogs = db.query(LaundryLog).order_by(LaundryLog.id.desc()).limit(5).all()
for l in lLogs:
    print(f"ID: {l.id}, Item: {l.item_id}, Qty: {l.quantity}, Status: {l.status}, Loc: {l.source_location_id}, Branch: {l.branch_id}")

print("\n--- BEDSHEET ITEM ---")
item = db.query(InventoryItem).filter(InventoryItem.name.ilike("%Bedsheet%")).first()
if item:
    print(f"ID: {item.id}, Name: {item.name}, Track Laundry: {item.track_laundry_cycle}, Cat ID: {item.category_id}")
    if item.category:
        print(f"Category Track Laundry: {item.category.track_laundry}")
else:
    print("Bedsheet not found")
