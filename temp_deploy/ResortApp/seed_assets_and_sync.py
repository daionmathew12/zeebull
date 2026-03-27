
import sys
import os
import random
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.inventory import Location, InventoryItem, AssetRegistry, InventoryCategory
from app.models.room import Room

def seed_assets_and_sync_rooms():
    db = SessionLocal()
    try:
        print("Starting Asset Seeding & Room Sync...")
        
        # 1. Ensure "Fixed Assets" Category exists
        cat_name = "Room Electronics & Furniture"
        category = db.query(InventoryCategory).filter(InventoryCategory.name == cat_name).first()
        if not category:
            category = InventoryCategory(
                name=cat_name,
                parent_department="Housekeeping",
                is_asset_fixed=True, # Important flag
                is_active=True
            )
            db.add(category)
            db.commit()
            db.refresh(category)
            print(f"Created Category: {category.name}")
            
        # 2. Ensure Asset Items exist
        asset_items_data = [
            {"name": "Smart TV 43-inch", "price": 25000},
            {"name": "Mini Fridge", "price": 12000},
            {"name": "Electric Kettle", "price": 1500},
            {"name": "Hair Dryer", "price": 1200},
            {"name": "Safe Locker", "price": 5000},
            {"name": "Study Table", "price": 8000},
            {"name": "Ergonomic Chair", "price": 4000}
        ]
        
        created_asset_items = {}
        for item_data in asset_items_data:
            item = db.query(InventoryItem).filter(InventoryItem.name == item_data["name"]).first()
            if not item:
                item = InventoryItem(
                    name=item_data["name"],
                    category_id=category.id,
                    unit="pcs",
                    unit_price=item_data["price"],
                    min_stock_level=0,
                    current_stock=0, # Assets are tracked individually, stock implies unassigned count
                    item_code=f"AST-{random.randint(1000,9999)}",
                    is_asset_fixed=True,
                    location="Main Warehouse"
                )
                db.add(item)
                db.commit()
                db.refresh(item)
                print(f"Created Asset Item: {item.name}")
            created_asset_items[item_data["name"]] = item

        # 3. Get all Guest Room Locations
        # We assume seed_diverse_rooms.py has run and created locations like "Room 101"
        room_locations = db.query(Location).filter(Location.location_type == "GUEST_ROOM").all()
        
        if not room_locations:
            print("No Guest Room locations found! Run seed_diverse_rooms.py first.")
            return

        print(f"Found {len(room_locations)} rooms to process.")

        # 4. Process each room
        for loc in room_locations:
            # A. SYNC TO ROOMS TABLE (For Booking System)
            # ------------------------------------------------
            # Extract number from name "Room 101" -> "101"
            room_num = loc.name.replace("Room ", "").strip()
            
            # Check if Room record exists
            room_record = db.query(Room).filter(Room.number == room_num).first()
            if not room_record:
                # Determine type/price based on seed_diverse_rooms logic
                r_type = loc.room_area # We stored type in room_area in previous script
                price = 3000 # Default
                if r_type == "Deluxe Room": price = 5000
                elif r_type == "Suite": price = 8000
                elif r_type == "Executive Suite": price = 12000
                elif r_type == "Presidential Suite": price = 25000
                
                room_record = Room(
                    number=room_num,
                    type=r_type,
                    price=price,
                    status="Available",
                    inventory_location_id=loc.id,
                    wifi=True,
                    air_conditioning=True,
                    bathroom=True
                )
                db.add(room_record)
                db.commit()
                print(f"  [Booking] synced Room {room_num}")
            else:
                # Ensure link is there
                if room_record.inventory_location_id != loc.id:
                    room_record.inventory_location_id = loc.id
                    db.commit()
                    print(f"  [Booking] Linked Room {room_num} to Location {loc.id}")
            
            # B. ASSIGN ASSETS (For Inventory System)
            # ------------------------------------------------
            # Define what goes in each room type
            assets_to_assign = ["Smart TV 43-inch", "Electric Kettle"]
            if "Deluxe" in loc.room_area or "Suite" in loc.room_area:
                assets_to_assign.extend(["Mini Fridge", "Hair Dryer", "Safe Locker"])
            if "Suite" in loc.room_area:
                assets_to_assign.extend(["Study Table", "Ergonomic Chair"])
                
            for asset_name in assets_to_assign:
                item = created_asset_items.get(asset_name)
                if not item: continue
                
                # Check if this asset type is already in the room
                existing = db.query(AssetRegistry).filter(
                    AssetRegistry.current_location_id == loc.id,
                    AssetRegistry.item_id == item.id
                ).first()
                
                if not existing:
                    # Create new asset instance tag
                    tag = f"{item.item_code}-{room_num}-{random.randint(10,99)}"
                    serial = f"SN{random.randint(100000,999999)}"
                    
                    new_asset = AssetRegistry(
                        asset_tag_id=tag,
                        item_id=item.id,
                        serial_number=serial,
                        current_location_id=loc.id,
                        status="active",
                        purchase_date=datetime.utcnow()
                    )
                    db.add(new_asset)
                    print(f"  [Asset] Assigned {asset_name} ({tag}) to {loc.name}")
        
        db.commit()
        print("\nAsset Seeding and Room Sync Completed Successfully!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_assets_and_sync_rooms()
