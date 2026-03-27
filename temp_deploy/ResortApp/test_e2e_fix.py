import requests
import sys
import os
import datetime

sys.path.append(os.getcwd())
try:
    from app.database import SessionLocal
    from app.utils.auth import create_access_token
    from app.models.user import User
    from app.models.inventory import Vendor, LocationStock, PurchaseMaster, InventoryTransaction
except ImportError:
    sys.path.append(os.path.join(os.getcwd(), 'ResortApp'))
    from app.database import SessionLocal
    from app.utils.auth import create_access_token
    from app.models.user import User
    from app.models.inventory import Vendor, LocationStock, PurchaseMaster, InventoryTransaction

def test_e2e_v3():
    db = SessionLocal()
    try:
        print("--- E2E Test Round 3 ---\n")
        user = db.query(User).first()
        role = user.role.name if user.role else 'admin'
        token = create_access_token(data={"user_id": user.id, "role": role})
        headers = {"Authorization": f"Bearer {token}"}
        vendor = db.query(Vendor).first()
        
        item_id = 20
        loc_id = 14
        
        ls = db.query(LocationStock).filter(LocationStock.location_id==loc_id, LocationStock.item_id==item_id).first()
        before = ls.quantity if ls else 0.0
        print(f"Stock Before: {before}")
        
        # Verify Last Transaction ID
        last_txn = db.query(InventoryTransaction).order_by(InventoryTransaction.id.desc()).first()
        last_txn_id_before = last_txn.id if last_txn else 0
        print(f"Last Txn ID Before: {last_txn_id_before}")

        payload = {
            "purchase_number": f"TEST-{datetime.datetime.now().strftime('%M%S')}",
            "vendor_id": vendor.id,
            "purchase_date": datetime.date.today().isoformat(),
            "status": "received",
            "destination_location_id": loc_id,
            "details": [{"item_id": item_id, "quantity": 5, "unit_price": 10, "unit": "pcs"}]
        }
        
        print("Sending request...")
        r = requests.post("http://127.0.0.1:8011/api/inventory/purchases", json=payload, headers=headers)
        print(f"Response: {r.status_code}")
        if r.status_code != 200: print(r.text)
        
        db.expire_all()
        
        # Check Stock
        ls = db.query(LocationStock).filter(LocationStock.location_id==loc_id, LocationStock.item_id==item_id).first()
        after = ls.quantity if ls else 0.0
        print(f"Stock After: {after}")
        
        # Check Transaction
        last_txn = db.query(InventoryTransaction).order_by(InventoryTransaction.id.desc()).first()
        last_txn_id_after = last_txn.id if last_txn else 0
        print(f"Last Txn ID After: {last_txn_id_after}")
        
        if last_txn_id_after > last_txn_id_before:
             print("Transaction Created: YES")
        else:
             print("Transaction Created: NO")

        if abs(after - (before + 5)) < 0.1:
            print("SUCCESS")
        else:
            print("FAILURE")

    except Exception:
        import traceback; traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_e2e_v3()
