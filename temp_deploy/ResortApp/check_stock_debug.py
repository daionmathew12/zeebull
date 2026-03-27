import sys
import os
sys.path.append('/var/www/inventory/ResortApp')
from app.database import SessionLocal
from app.models.inventory import Location, LocationStock, InventoryItem
from app.models.room import Room

db = SessionLocal()
print("--- DEBUG START ---")
room = db.query(Room).filter(Room.number == '101').first()
if room:
    print(f"Room 101 found. Inventory Location ID: {room.inventory_location_id}")
    if room.inventory_location_id:
        loc_id = room.inventory_location_id
        stocks = db.query(LocationStock).filter(LocationStock.location_id == loc_id).all()
        print(f"Found {len(stocks)} stocks in Location {loc_id}")
        for s in stocks:
            item = db.query(InventoryItem).filter(InventoryItem.id == s.item_id).first()
            if not item:
                 # Try old import style if implied
                 pass
            name = item.name if item else "UNKNOWN"
            print(f"Stock ID: {s.id}, Item ID: {s.item_id}, Name: {name}, Qty: {s.quantity}")
    else:
        print("No inventory location ID")
else:
    print("Room 101 not found")
print("--- DEBUG END ---")
