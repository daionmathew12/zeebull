from app.database import SessionLocal
from app.models.checkout import CheckoutRequest
import json

db = SessionLocal()
request = db.query(CheckoutRequest).filter(CheckoutRequest.room_number == "101", CheckoutRequest.status == "completed").order_by(CheckoutRequest.id.desc()).first()

if request:
    data = request.inventory_data
    for item in data:
        if "TV" in item['item_name']:
            item['missing_qty'] = 1.0
            item['missing_item_charge'] = 2000.0 # Will be recalculated by my new logic anyway
            item['is_fixed_asset'] = True
        if "LED Bulb" in item['item_name']:
            item['damage_qty'] = 1.0
            item['damage_charge'] = 50.0
            item['is_rentable'] = True
    
    request.inventory_data = data
    db.commit()
    print(f"Updated Checkout Request {request.id} with damages.")
else:
    print("No completed checkout request found to update.")

db.close()
