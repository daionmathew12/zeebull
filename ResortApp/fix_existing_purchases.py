#!/usr/bin/env python3
"""
Fix existing received purchases to update their destination location stocks.
This is a one-time fix for purchases that were received before the location stock update was added.
"""

from app.database import SessionLocal
from app.models.inventory import PurchaseMaster, PurchaseDetail, LocationStock
from datetime import timezone, datetime

db = SessionLocal()

print("🔧 Fixing existing received purchases...")
print("=" * 60)

# Find all received purchases
received_purchases = db.query(PurchaseMaster).filter(
    PurchaseMaster.status == "received"
).all()

print(f"\nFound {len(received_purchases)} received purchases\n")

fixed_count = 0
for purchase in received_purchases:
    if not purchase.destination_location_id:
        print(f"⚠️  {purchase.purchase_number}: No destination location, skipping")
        continue
    
    print(f"📦 {purchase.purchase_number} → {purchase.destination_location.name if purchase.destination_location else 'Unknown'}")
    
    details = db.query(PurchaseDetail).filter(
        PurchaseDetail.purchase_master_id == purchase.id
    ).all()
    
    for detail in details:
        item_name = detail.item.name if detail.item else f"Item #{detail.item_id}"
        
        # Check if location stock already exists
        loc_stock = db.query(LocationStock).filter(
            LocationStock.location_id == purchase.destination_location_id,
            LocationStock.item_id == detail.item_id
        ).first()
        
        if loc_stock:
            print(f"   ℹ️  {item_name}: Already in location stock ({loc_stock.quantity}), skipping")
        else:
            # Add to location stock
            loc_stock = LocationStock(
                location_id=purchase.destination_location_id,
                item_id=detail.item_id,
                quantity=detail.quantity,
                last_updated=datetime.now(timezone.utc)
            )
            db.add(loc_stock)
            print(f"   ✅ {item_name}: Added {detail.quantity} to location stock")
            fixed_count += 1

db.commit()

print("\n" + "=" * 60)
print(f"✅ Fixed {fixed_count} location stock entries!")
print("\n💡 Future purchases will automatically update location stock when received")

db.close()
