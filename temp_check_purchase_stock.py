import os
import sys

# Force UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add the project root to sys.path
sys.path.append(os.path.join(os.getcwd(), "ResortApp"))

from app.database import SessionLocal
from app.models.inventory import InventoryItem, LocationStock, PurchaseMaster, PurchaseDetail

def check_stock():
    db = SessionLocal()
    try:
        # Let's find 'asdfg' (since the user likely recreated it)
        items = db.query(InventoryItem).filter(InventoryItem.name == "asdfg").all()
        for item in items:
            print(f"Item ID: {item.id}, Name: {item.name}, Branch: {item.branch_id}, Stock: {item.current_stock}")
            stocks = db.query(LocationStock).filter(LocationStock.item_id == item.id).all()
            for st in stocks:
                print(f"  -> LocationStock loc: {st.location_id}, qty: {st.quantity}, branch: {st.branch_id}")
            
            p_details = db.query(PurchaseDetail).filter(PurchaseDetail.item_id == item.id).all()
            for pd in p_details:
                pm = db.query(PurchaseMaster).filter(PurchaseMaster.id == pd.purchase_master_id).first()
                print(f"  -> Purchase: {pm.purchase_number}, Status: {pm.status}, dest: {pm.destination_location_id}, branch: {pm.branch_id}, pd_qty: {pd.quantity}")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_stock()
