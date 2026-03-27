
import sys
import os
sys.path.append(os.getcwd())
from app.database import SessionLocal
from app.models.checkout import Checkout
import json

db = SessionLocal()
c = db.query(Checkout).filter(Checkout.id == 4).first()
if c:
    data = {
        "id": c.id,
        "grand_total": float(c.grand_total or 0),
        "room_total": float(c.room_total or 0),
        "food_total": float(c.food_total or 0),
        "service_total": float(c.service_total or 0),
        "consumables_charges": float(c.consumables_charges or 0),
        "asset_damage_charges": float(c.asset_damage_charges or 0),
        "tax_amount": float(c.tax_amount or 0),
        "discount_amount": float(c.discount_amount or 0),
        "bill_details": c.bill_details
    }
    print(json.dumps(data, indent=2))
else:
    print("Checkout not found")
