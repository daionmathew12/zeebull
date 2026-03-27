from app.database import SessionLocal
from app.models.inventory import InventoryItem

def debug():
    db = SessionLocal()
    try:
        item = db.query(InventoryItem).filter(InventoryItem.id == 4).first()
        if item:
            print(f"Name: {item.name}")
            print(f"Category: {item.category.name if item.category else 'None'}")
            print(f"Is Rentable: {item.is_rentable}")
            print(f"Is sellable: {item.is_sellable_to_guest}")
            print(f"Limit: {item.complimentary_limit}")
    finally:
        db.close()

if __name__ == "__main__":
    debug()
