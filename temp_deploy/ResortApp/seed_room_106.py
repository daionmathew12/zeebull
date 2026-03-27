from datetime import datetime
from app.database import SessionLocal
from app.models.inventory import LocationStock, AssetRegistry, InventoryItem

db = SessionLocal()

def seed_room_106():
    print("Seeding Room 106 (Location ID 15)...")
    
    location_id = 15

    # 1. Add Consumables (LocationStock)
    consumables = [
        {"id": 8, "name": "Premium Mineral Water 1 Liter", "qty": 4.0}, # 4 bottles
        {"id": 16, "name": "Coca Cola 300ml", "qty": 4.0} # 4 cans
    ]

    for c in consumables:
        print(f"Adding/Updating {c['name']} (ID {c['id']})...")
        stock = db.query(LocationStock).filter(
            LocationStock.location_id == location_id, 
            LocationStock.item_id == c['id']
        ).first()
        
        if not stock:
            stock = LocationStock(
                location_id=location_id,
                item_id=c['id'],
                quantity=c['qty']
            )
            db.add(stock)
            print(f"- Created new stock record: {c['qty']}x {c['name']}")
        else:
            stock.quantity = c['qty']
            print(f"- Updated stock record: {c['qty']}x {c['name']}")

    # 2. Add Fixed Assets (AssetRegistry)
    assets = [
        {"id": 13, "name": "TV", "prefix": "TV-RM106", "serial_prefix": "LG"},
        {"id": 6, "name": "Professional Frying Pan", "prefix": "PAN-RM106", "serial_prefix": "TEFAL"}
    ]

    for a in assets:
        print(f"Adding {a['name']} (ID {a['id']}) to AssetRegistry...")
        # Check if a serialized asset of this type already exists in this room
        asset = db.query(AssetRegistry).filter(
            AssetRegistry.current_location_id == location_id,
            AssetRegistry.item_id == a['id']
        ).first()

        if not asset:
            import time
            time.sleep(1.1)
            timestamp = int(datetime.now().timestamp())
            try:
                asset = AssetRegistry(
                    asset_tag_id=f"{a['prefix']}-{timestamp}",
                    item_id=a['id'],
                    serial_number=f"{a['serial_prefix']}-{timestamp}",
                    current_location_id=location_id,
                    status="active"
                )
                db.add(asset)
                db.commit() # Commit each one
                print(f"- Created new asset: {a['name']}")
            except Exception as e:
                db.rollback()
                print(f"- Failed to add asset {a['name']}: {str(e)}")
        else:
            print(f"- {a['name']} already exists in room")

    db.commit()
    print("Seeding of Room 106 complete.")

if __name__ == "__main__":
    seed_room_106()
