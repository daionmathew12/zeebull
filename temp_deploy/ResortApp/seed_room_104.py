from datetime import datetime
from app.database import SessionLocal
from app.models.inventory import LocationStock, AssetRegistry, InventoryItem

db = SessionLocal()

def seed_room_104():
    print("Seeding Room 104 (Location ID 10)...")
    
    # 1. Add Consumables (LocationStock)
    # Item ID 8: Premium Mineral Water 1 Liter
    print("Adding Mineral Water (ID 8) to LocationStock...")
    stock = db.query(LocationStock).filter(
        LocationStock.location_id == 10, 
        LocationStock.item_id == 8
    ).first()
    
    if not stock:
        stock = LocationStock(
            location_id=10,
            item_id=8,
            quantity=2.0
        )
        db.add(stock)
        print("- Created new stock record: 2x Mineral Water")
    else:
        stock.quantity = 2.0
        print("- Updated stock record: 2x Mineral Water")

    # 2. Add Fixed Asset (AssetRegistry)
    # Item ID 13: TV
    print("Adding TV (ID 13) to AssetRegistry...")
    # Check if a serialized TV already exists in this room
    asset = db.query(AssetRegistry).filter(
        AssetRegistry.current_location_id == 10,
        AssetRegistry.item_id == 13
    ).first()

    if not asset:
        asset = AssetRegistry(
            asset_tag_id=f"TV-RM104-{int(datetime.now().timestamp())}",
            item_id=13,
            serial_number=f"LG-{int(datetime.now().timestamp())}",
            current_location_id=10,
            status="active"
        )
        db.add(asset)
        print("- Created new asset: TV")
    else:
        print("- TV asset already exists in room")

    db.commit()
    print("Seeding complete.")

if __name__ == "__main__":
    seed_room_104()
