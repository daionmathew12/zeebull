from app.database import SessionLocal
from app.models.inventory import InventoryItem

db = SessionLocal()
items = db.query(InventoryItem).all()
print(f"Total items: {len(items)}")
for item in items:
    print(f"ID: {item.id}, Name: {item.name}")
db.close()
