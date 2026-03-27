import sys
import os
sys.path.append('/var/www/inventory/ResortApp')
from app.database import SessionLocal
from app.models.checkout import CheckoutRequest
from app.api.checkout import get_checkout_request_inventory_details

db = SessionLocal()
# Query locally to confirm we get the right one
req = db.query(CheckoutRequest).filter(CheckoutRequest.room_number == '101').order_by(CheckoutRequest.id.desc()).first()
if req:
    print(f"Testing Request ID: {req.id}")
    try:
        res = get_checkout_request_inventory_details(req.id, db)
        print("RESULT keys:", res.keys())
        if 'error' in res:
            print("ERROR RETURNED:", res['error'])
        else:
            items = res.get('items', [])
            print(f"Items count: {len(items)}")
            for i in items:
                print(f" - {i.get('item_name')} ({i.get('current_stock')})")
            
            if len(items) == 0:
                 print("Zero items returned. Checking logic...")
    except Exception as e:
        print("EXCEPTION calling function:", e)
        import traceback
        traceback.print_exc()
else:
    print("No request found for 101")
