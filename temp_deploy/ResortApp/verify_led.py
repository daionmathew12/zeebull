import sys
import os
import json
sys.path.append('/var/www/inventory/ResortApp')
from app.database import SessionLocal
from app.models.checkout import CheckoutRequest
from app.api.checkout import get_checkout_request_inventory_details

db = SessionLocal()
req = db.query(CheckoutRequest).filter(CheckoutRequest.room_number == '101').order_by(CheckoutRequest.id.desc()).first()
if req:
    res = get_checkout_request_inventory_details(req.id, db)
    items = res.get('items', [])
    for item in items:
        if 'LED' in item.get('item_name', ''):
             print(f"Name: {item.get('item_name')}")
             print(f"Type: {item.get('item_type')}")
             print(f"IsRentable: {item.get('is_rentable')}")
             print(f"IsFixed: {item.get('is_fixed_asset')}")
