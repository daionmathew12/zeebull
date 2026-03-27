from app.database import SessionLocal
from app.models.inventory import InventoryItem

def check():
    db = SessionLocal()
    items = db.query(InventoryItem).filter(InventoryItem.name.ilike('%Bulb%')).all()
    for i in items:
        print(f"ID:{i.id} | Name:{i.name}")
    db.close()

if __name__ == "__main__":
    check()
