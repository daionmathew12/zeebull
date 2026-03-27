from app.database import SessionLocal
from app.curd.inventory import create_stock_issue
from app.models.inventory import InventoryItem, InventoryCategory, Location
from datetime import datetime

# Setup
db = SessionLocal()

try:
    # 1. Ensure we have an Item and Location
    item = db.query(InventoryItem).first()
    if not item:
        cat = Category(name="Test Cat")
        db.add(cat)
        db.commit()
        item = InventoryItem(name="Test Item 2", category_id=cat.id, unit_price=10.5)
        db.add(item)
        db.commit()
    
    loc = db.query(Location).filter(Location.location_type == "GUEST_ROOM").first()
    if not loc:
        # Create Guest Room location
        loc = Location(name="Room 999", location_type="GUEST_ROOM", room_area="999", is_active=True)
        db.add(loc)
        db.commit()
        print(f"Created location Room 999 with ID {loc.id}")

    print(f"Using Item ID: {item.id} (Price: {item.unit_price}, Type: {type(item.unit_price)})")
    print(f"Using Location ID: {loc.id}")

    # 2. Prepare Data for create_stock_issue
    data = {
        "source_location_id": 1, # Assuming 1 is main
        "destination_location_id": loc.id,
        "details": [
            {
                "item_id": item.id,
                "quantity": 1, # Integer/Float
                "unit": "pcs",
                "notes": "Test Allocation"
            }
        ],
        "notes": "Test Allocation Check"
    }

    # 3. Call the function
    print("Calling create_stock_issue...")
    try:
        from app.curd.inventory import create_stock_issue
        issue = create_stock_issue(db, data, issued_by=1)
        print(f"Success! Issue ID: {issue.id}")
    except Exception as e:
        print(f"FAILED with error: {e}")
        import traceback
        traceback.print_exc()

finally:
    db.close()
