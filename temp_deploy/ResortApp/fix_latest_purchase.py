#!/usr/bin/env python3
"""Manually fix the latest purchase to add items to location stock"""

from app.database import SessionLocal
from app.models.inventory import PurchaseMaster, PurchaseDetail, LocationStock
from datetime import datetime

db = SessionLocal()

# Get latest purchase
purchase = db.query(PurchaseMaster).order_by(PurchaseMaster.id.desc()).first()

if not purchase or purchase.status != "received":
    print("No received purchase to fix")
    db.close()
    exit()

print(f"Fixing purchase: {purchase.purchase_number}")
print(f"Destination: {purchase.destination_location.name if purchase.destination_location else 'None'}")

if not purchase.destination_location_id:
    print("No destination location!")
    db.close()
    exit()

# Get purchase items
details = db.query(PurchaseDetail).filter(
    PurchaseDetail.purchase_master_id == purchase.id
).all()

fixed = 0
for detail in details:
    item_name = detail.item.name if detail.item else f"Item #{detail.item_id}"
    
    # Check if already in location stock
    loc_stock = db.query(LocationStock).filter(
        LocationStock.location_id == purchase.destination_location_id,
        LocationStock.item_id == detail.item_id
    ).first()
    
    if loc_stock:
        print(f"  ℹ️  {item_name}: Already in stock ({loc_stock.quantity})")
    else:
        # Add to location stock
        loc_stock = LocationStock(
            location_id=purchase.destination_location_id,
            item_id=detail.item_id,
            quantity=detail.quantity,
            last_updated=datetime.utcnow()
        )
        db.add(loc_stock)
        print(f"  ✅ {item_name}: Added {detail.quantity} to location")
        fixed += 1

db.commit()
print(f"\n✅ Fixed {fixed} items!")
db.close()
