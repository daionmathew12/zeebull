import sys
import os
import json
sys.path.append('/var/www/inventory/ResortApp')
from app.database import SessionLocal
from app.models.checkout import CheckoutRequest
from app.api.checkout import get_checkout_request_inventory_details

# Function to serialize datetime/etc
def default(o):
    return str(o)

db = SessionLocal()
req = db.query(CheckoutRequest).filter(CheckoutRequest.room_number == '101').order_by(CheckoutRequest.id.desc()).first()
if req:
    print(f"REQ_ID:{req.id}")
    try:
        res = get_checkout_request_inventory_details(req.id, db)
        items = res.get('items', [])
        print(json.dumps(items, default=default, indent=2))
    except Exception as e:
        print("ERROR:", e)
else:
    print("NO_REQ")
