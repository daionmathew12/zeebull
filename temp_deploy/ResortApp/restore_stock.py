from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.inventory import InventoryItem

def restore_stock():
    db = SessionLocal()
    try:
        # Items to restore
        items_to_fix = ["Coca Cola 750ml", "Mineral Water 1L"]
        
        print("Restoring stock for impacted items...")
        
        for name in items_to_fix:
            item = db.query(InventoryItem).filter(InventoryItem.name == name).first()
            if item:
                print(f"Found {item.name}. Current Stock: {item.current_stock}")
                # Restore to a safe default, e.g., 100, or try to calculcate from purchase? 
                # Since we don't know exact history, setting to a healthy testing amount (e.g. 50 or 100) is best.
                # Let's set to 50 as seen in previous issues or just 100 to be safe.
                if item.current_stock == 0:
                    item.current_stock = 100.0
                    print(f" -> UPDATED {item.name} stock to 100.0")
                else:
                    print(f" -> Skipping {item.name}, stock is not 0 ({item.current_stock})")
            else:
                print(f"Item {name} not found.")
        
        db.commit()
        print("Stock restoration complete.")
        
    except Exception as e:
        print(f"Error restoring stock: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    restore_stock()
