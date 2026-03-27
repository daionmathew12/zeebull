from app.database import SessionLocal
from app.models.inventory import InventoryItem, InventoryCategory

def check_cat():
    db = SessionLocal()
    item = db.query(InventoryItem).filter(InventoryItem.id == 3).first()
    if item and item.category:
        print(f"Item: {item.name}, Category: {item.category.name}, is_asset_fixed (cat): {item.category.is_asset_fixed}")
    db.close()

if __name__ == "__main__":
    check_cat()
