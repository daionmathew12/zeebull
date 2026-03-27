from app.database import SessionLocal
from app.models.inventory import InventoryItem, AssetMapping, LocationStock, Location

db = SessionLocal()

def fix_light_item():
    print("Fixing 'light' item...")
    
    # 1. Update Item Definition
    item = db.query(InventoryItem).filter(InventoryItem.name == "light").first()
    if item:
        print(f"Updating '{item.name}' (ID: {item.id}) to be an Fixed Asset.")
        item.is_asset_fixed = True
        item.type = "asset" # If there's a type string, though usually it's boolean flags
        db.add(item)
    else:
        print("Item 'light' not found!")
        return

    # 2. Consolidate LocationStock into AssetMappings for Room 101
    room_101 = db.query(Location).filter(Location.name == "Room 101").first()
    if room_101:
        print(f"Processing Room 101 (ID: {room_101.id})...")
        
        # Check for Stock
        stock_entry = db.query(LocationStock).filter(
            LocationStock.location_id == room_101.id,
            LocationStock.item_id == item.id
        ).first()
        
        if stock_entry:
            print(f"Found Stock entry: Qty {stock_entry.quantity}. converting to Asset Mapping...")
            
            # Create equivalent Asset Mapping
            # AssetMapping usually has quantity 1 per row for serialization, but can have quantity field
            new_asset = AssetMapping(
                item_id=item.id,
                location_id=room_101.id,
                quantity=stock_entry.quantity,
                notes="Converted from Stock"
            )
            db.add(new_asset)
            
            # Remove Stock entry
            db.delete(stock_entry)
            print("Deleted Stock entry.")
        else:
            print("No Stock entry found in Room 101.")

        # 3. Cleanup Duplicate Asset Mappings (Optional but good)
        # If we have multiple rows with same item/location and no serial number, we could merge them?
        # Or just leave them as individual instances (which is typical for assets).
        # The user saw "2" assets. Now they might see "3" assets (2 original + 1 converted).
        # This is logically consistent: 3 lights in the room.
    
    db.commit()
    print("Fix complete.")

if __name__ == "__main__":
    fix_light_item()
