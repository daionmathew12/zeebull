from app.database import SessionLocal
from app.models.inventory import InventoryItem

def fix_data():
    db = SessionLocal()
    try:
        # Fix Mineral Water limit
        items = db.query(InventoryItem).filter(InventoryItem.name.ilike("%mineral water%")).all()
        for item in items:
            print(f"Updating {item.name}: {item.complimentary_limit} -> 2")
            item.complimentary_limit = 2
        
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    fix_data()
