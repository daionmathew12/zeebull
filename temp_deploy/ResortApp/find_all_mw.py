from app.database import SessionLocal
from app.models.inventory import InventoryItem

def debug():
    db = SessionLocal()
    try:
        items = db.query(InventoryItem).filter(InventoryItem.name.ilike("%mineral water%")).all()
        for item in items:
            print(f"ID: {item.id}, Name: {item.name}, Limit: {item.complimentary_limit}")
    finally:
        db.close()

if __name__ == "__main__":
    debug()
