import sys
import os
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.inventory import InventoryItem, LocationStock
from app.models.room import Room

db = SessionLocal()

try:
    print("Checking Room 103 Stock...")
    room = db.query(Room).filter(Room.number == "103").first()
    if not room:
        print("Room 103 not found")
        sys.exit(1)
        
    loc_id = room.inventory_location_id
    print(f"Location ID: {loc_id}")

    # Define Items that SHOULD have LocationStock (Consumables only)
    # Assets (TV, Kettle) are in AssetRegistry, so we DELETE their LocationStock to prevent duplicates
    valid_consumables = ["Coca Cola", "Mineral Water"]
    
    valid_ids = []
    for name in valid_consumables:
        item = db.query(InventoryItem).filter(InventoryItem.name == name).first()
        if item:
            valid_ids.append(item.id)
            print(f"Valid Item: {name} (ID {item.id})")
        else:
            print(f"WARNING: Valid Item {name} NOT FOUND in DB")

    stocks = db.query(LocationStock).filter(LocationStock.location_id == loc_id).all()
    print(f"Found {len(stocks)} stock records.")
    
    seen_ids = set()
    deleted_count = 0
    
    for s in stocks:
        item_name = s.item.name if s.item else "Unknown"
        should_keep = False
        
        if s.item_id in valid_ids:
            if s.item_id not in seen_ids:
                should_keep = True
                seen_ids.add(s.item_id)
            else:
                print(f"DUPLICATE ROW for {item_name} (ID {s.item_id}) - Deleting")
        else:
            print(f"UNWANTED ITEM {item_name} (ID {s.item_id}) - Deleting (Likely Asset or Old Duplicate)")
            
        if not should_keep:
            db.delete(s)
            deleted_count += 1
        else:
            print(f"KEEPING {item_name} (ID {s.item_id}) - Qty {s.quantity}")
            
    db.commit()
    print(f"Cleanup Complete. Deleted {deleted_count} records.")

except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
