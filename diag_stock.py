import os
import sys

# Add the project root to sys.path
sys.path.append(os.path.join(os.getcwd(), "ResortApp"))

from app.database import SessionLocal
from app.models.inventory import InventoryItem, InterBranchTransfer

def check_stock():
    db = SessionLocal()
    try:
        # Check transfers
        transfers = db.query(InterBranchTransfer).all()
        print("--- TRANSFERS ---")
        for t in transfers:
            print(f"ID: {t.id}, Num: {t.transfer_number}, Status: {t.status}, Item: {t.item_id}, Source: {t.source_branch_id}, Dest: {t.destination_branch_id}")
        
        # Check items named 'asdfg'
        items = db.query(InventoryItem).filter(InventoryItem.name.ilike('%asdfg%')).all()
        print("\n--- ITEMS ---")
        for i in items:
            print(f"ID: {i.id}, Name: {i.name}, Branch: {i.branch_id}, Stock: {i.current_stock}, Code: {i.item_code}")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_stock()
