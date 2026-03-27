"""
Fix Smart TV in Room 103 - Remove from location stock after damage
"""
from app.database import SessionLocal
from app.models.inventory import LocationStock, Location, InventoryItem
from datetime import datetime

db = SessionLocal()

try:
    # Find Room 103's location
    room_103_loc = db.query(Location).filter(
        Location.name.ilike("%Room 103%")
    ).first()
    
    if not room_103_loc:
        print("❌ Room 103 location not found")
        exit(1)
    
    print(f"✅ Found Room 103 location: {room_103_loc.name} (ID: {room_103_loc.id})")
    
    # Find Smart TV item
    smart_tv = db.query(InventoryItem).filter(
        InventoryItem.name.ilike("%Smart TV%43%")
    ).first()
    
    if not smart_tv:
        print("❌ Smart TV 43-inch not found")
        exit(1)
    
    print(f"✅ Found Smart TV: {smart_tv.name} (ID: {smart_tv.id})")
    
    # Find location stock
    loc_stock = db.query(LocationStock).filter(
        LocationStock.location_id == room_103_loc.id,
        LocationStock.item_id == smart_tv.id
    ).first()
    
    if not loc_stock:
        print("❌ No location stock found for Smart TV in Room 103")
        exit(1)
    
    print(f"📦 Current stock: {loc_stock.quantity}")
    
    if loc_stock.quantity > 0:
        # Deduct the damaged TV
        loc_stock.quantity -= 1
        loc_stock.last_updated = datetime.utcnow()
        db.commit()
        print(f"✅ Deducted 1 Smart TV from Room 103. New stock: {loc_stock.quantity}")
    else:
        print("⚠️  Stock is already 0, no deduction needed")
    
    print("\n✅ Fix completed successfully!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    db.rollback()
finally:
    db.close()
