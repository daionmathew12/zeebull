from app.database import SessionLocal
from app.models.inventory import LocationStock

db = SessionLocal()

# Create a test location stock entry
test_stock = LocationStock(
    location_id=1,  # Central Warehouse
    item_id=1,      # First item
    quantity=100
)

db.add(test_stock)
db.commit()

print("✅ Test location stock created!")
print(f"Location: 1, Item: 1, Quantity: 100")

# Verify
stocks = db.query(LocationStock).all()
print(f"\nTotal location stocks: {len(stocks)}")
for s in stocks:
    print(f"  Location {s.location_id}, Item {s.item_id}: {s.quantity}")

db.close()
