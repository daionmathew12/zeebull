
import sys
import os

# Add root directory to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.inventory import InventoryItem

def fix_waste_stock():
    db = SessionLocal()
    try:
        print("--- Deducting Stock for Waste Logs (Fixing Mismatch) ---")
        
        # 1. Test Asset Flow Item (Transaction 144, Qty 1)
        item1 = db.query(InventoryItem).filter(InventoryItem.name == "Test Asset Flow Item").first()
        if item1:
            print(f"Deducting 1.0 from '{item1.name}' (Current: {item1.current_stock})")
            item1.current_stock -= 1.0
        
        # 2. light (Transaction 92, Qty 1)
        item2 = db.query(InventoryItem).filter(InventoryItem.name == "light").first()
        if item2:
             print(f"Deducting 1.0 from '{item2.name}' (Current: {item2.current_stock})")
             item2.current_stock -= 1.0

        db.commit()
        print("Stock manually corrected.")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_waste_stock()
