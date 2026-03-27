
import sys
import os

# Add root directory to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.inventory import InventoryItem

def fix_waste_stock_2():
    db = SessionLocal()
    try:
        print("--- Deducting Remaining Stock for Waste Logs ---")
        
        # 1. Test Asset Flow Item (Transaction 141 and 144 - we did one, need another)
        item1 = db.query(InventoryItem).filter(InventoryItem.name == "Test Asset Flow Item").first()
        if item1:
            print(f"Deducting Another 1.0 from '{item1.name}' (Current: {item1.current_stock})")
            item1.current_stock -= 1.0
        
        db.commit()
        print("Stock manually corrected 2nd pass.")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_waste_stock_2()
