import os
import sys

# Force UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add the project root to sys.path
sys.path.append(os.path.join(os.getcwd(), "ResortApp"))

from app.database import SessionLocal
from app.models.inventory import InventoryItem, InventoryTransaction, LocationStock

def delete_dupes():
    db = SessionLocal()
    try:
        items = db.query(InventoryItem).filter(InventoryItem.name == "asdfg").all()
        print(f"Found {len(items)} items named 'asdfg'. Deleting...")
        for item in items:
            # Delete associated transactions
            db.query(InventoryTransaction).filter(InventoryTransaction.item_id == item.id).delete()
            # Delete associated location stocks
            db.query(LocationStock).filter(LocationStock.item_id == item.id).delete()
            # Delete the item
            db.delete(item)
        db.commit()
        print("Deleted duplicate items successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    delete_dupes()
