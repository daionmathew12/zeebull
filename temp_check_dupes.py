import os
import sys

# Force UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add the project root to sys.path
sys.path.append(os.path.join(os.getcwd(), "ResortApp"))

from app.database import SessionLocal
from app.models.inventory import InventoryItem

def check_dupes():
    db = SessionLocal()
    try:
        items = db.query(InventoryItem).filter(InventoryItem.name == "asdfg").all()
        print(f"Found {len(items)} items named 'asdfg':")
        for item in items:
            print(f"- ID: {item.id}, Name: {item.name}, Branch ID: {item.branch_id}, Active: {item.is_active}")
        
        all_items = db.query(InventoryItem).all()
        print(f"Total items in DB: {len(all_items)}")
    finally:
        db.close()

if __name__ == "__main__":
    check_dupes()
