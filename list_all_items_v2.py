import os
import sys
sys.path.append(os.path.join(os.getcwd(), "ResortApp"))
from app.database import SessionLocal
from app.models.inventory import InventoryItem

def list_all_items():
    db = SessionLocal()
    try:
        # Check by name, case insensitive, and branch_id
        items = db.query(InventoryItem).all()
        print(f"Total items in DB: {len(items)}")
        for i in items:
            print(f"ID: {i.id}, Name: {i.name}, Branch: {i.branch_id}, Stock: {i.current_stock}, Code: {i.item_code}")
    finally:
        db.close()

if __name__ == "__main__":
    list_all_items()
