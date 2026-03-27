
import sys
import os

# Add root directory to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.inventory import StockIssue, InventoryItem

def restore_transferred_stock():
    db = SessionLocal()
    try:
        print("--- Restoring Stock for Transfer Issues (Fixing Global Count) ---")
        
        # Limit to Issue 12 for safety as confirmed case
        issues = db.query(StockIssue).filter(
            StockIssue.id == 12,
            StockIssue.destination_location_id != None
        ).all()
        
        for issue in issues:
            print(f"Processing Stock Issue #{issue.id} (Transfer)")
            for detail in issue.details:
                item = db.query(InventoryItem).get(detail.item_id)
                if item:
                    print(f"  - Item: {item.name} | Qty Restored: +{detail.issued_quantity}")
                    item.current_stock += detail.issued_quantity
                    
        db.commit()
        print("Stock counts restored.")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    restore_transferred_stock()
