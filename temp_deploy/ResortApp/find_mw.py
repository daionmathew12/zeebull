from app.database import SessionLocal
from app.models.inventory import InventoryItem

def debug():
    db = SessionLocal()
    try:
        item = db.query(InventoryItem).filter(InventoryItem.name.ilike("%mineral water%")).first()
        if item:
            print(f"Name: {item.name}, ID: {item.id}, Limit: {item.complimentary_limit}")
        else:
            print("Mineral Water NOT FOUND")
    finally:
        db.close()

if __name__ == "__main__":
    debug()
