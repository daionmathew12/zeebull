"""
Backfill location stocks for all received purchases
"""
from app.database import SessionLocal
from app.models.inventory import PurchaseMaster, LocationStock

db = SessionLocal()

# Get all received purchases with a destination location
purchases = db.query(PurchaseMaster).filter(
    PurchaseMaster.status == "received",
    PurchaseMaster.destination_location_id.isnot(None)
).all()

print(f"Found {len(purchases)} received purchases with destination locations")

for purchase in purchases:
    print(f"\nProcessing {purchase.purchase_number}...")
    print(f"  Destination: Location {purchase.destination_location_id}")
    print(f"  Details: {len(purchase.details)} items")
    
    for detail in purchase.details:
        if not detail.item_id:
            continue
        
        # Check if location stock already exists
        existing = db.query(LocationStock).filter(
            LocationStock.location_id == purchase.destination_location_id,
            LocationStock.item_id == detail.item_id
        ).first()
        
        if existing:
            print(f"    Item {detail.item_id}: Already exists, adding {detail.quantity} to {existing.quantity}")
            existing.quantity += detail.quantity
        else:
            print(f"    Item {detail.item_id}: Creating new stock with qty {detail.quantity}")
            new_stock = LocationStock(
                location_id=purchase.destination_location_id,
                item_id=detail.item_id,
                quantity=detail.quantity
            )
            db.add(new_stock)

db.commit()
print("\n✅ Backfill complete!")

# Show results
stocks = db.query(LocationStock).all()
print(f"\nTotal location stocks: {len(stocks)}")
for s in stocks:
    print(f"  Location {s.location_id}, Item {s.item_id}: {s.quantity}")

db.close()
