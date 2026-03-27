import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.inventory import (
    PurchaseMaster, PurchaseDetail, LocationStock, 
    InventoryItem, InventoryTransaction
)

def clear_recent_data():
    db = SessionLocal()
    try:
        print("--- Clearing Recent Inventory Data (Correct Order) ---")
        
        # 1. Transactions (Child of almost everything)
        print("1. Deleting ALL Inventory Transactions...")
        db.query(InventoryTransaction).delete()
        
        # 2. Purchase Details (Child of Purchase Master)
        print("2. Deleting ALL Purchase Details...")
        db.query(PurchaseDetail).delete()
        
        # 3. Purchase Master
        print("3. Deleting ALL Purchase Masters...")
        db.query(PurchaseMaster).delete()
        
        # 4. Location Stock
        print("4. Resetting Location Stock...")
        db.query(LocationStock).delete()
        
        # 5. Global Stock
        print("5. Resetting Global Item Stock...")
        items = db.query(InventoryItem).all()
        for item in items:
            item.current_stock = 0.0
            
        db.commit()
        print("SUCCESS: Inventory data cleared. Stocks reset to 0.")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clear_recent_data()
