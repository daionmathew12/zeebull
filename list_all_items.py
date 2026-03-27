import os
import sys
sys.path.append(os.path.join(os.getcwd(), "ResortApp"))
from app.database import SessionLocal
from app.models.inventory import InventoryItem

def list_all_items():
    db = SessionLocal()
    try:
        items = db.query(InventoryItem).all()
        for i in items:
            print(f"ID: {i.id}, Name: {i.name}, Branch: {i.branch_id}, Stock: {i.current_stock}")
    finally:
        db.close()

if __name__ == "__main__":
    list_all_items()
