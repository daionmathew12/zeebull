import sys
import os
from datetime import datetime
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.inventory import InventoryItem, Location, LocationStock

db = SessionLocal()
print("SEEDING STOCK...")

try:
    items = db.query(InventoryItem).all()
    if not items:
        print("No items found.")
    else:
        warehouse = db.query(Location).filter(Location.location_type.in_(["WAREHOUSE", "CENTRAL_WAREHOUSE"])).first()
        wh_id = warehouse.id if warehouse else None
        print(f"Warehouse ID: {wh_id}")
        
        for item in items:
            item.current_stock = 100.0
            if not item.unit_price: item.unit_price = 10.0
            
            if wh_id:
                existing = db.query(LocationStock).filter(LocationStock.location_id == wh_id, LocationStock.item_id == item.id).first()
                if existing:
                    existing.quantity = 100.0
                else:
                    db.add(LocationStock(location_id=wh_id, item_id=item.id, quantity=100.0, last_updated=datetime.utcnow()))

        db.commit()
        print("SUCCESS: Stock replenished.")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
