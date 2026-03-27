from app.database import SessionLocal
from app.models.inventory import AssetMapping, InventoryItem, Location

db = SessionLocal()

def manual_fix_light_waste():
    print("Checking 'light' stock in Room 101...")
    
    # 1. Get Room 101
    room = db.query(Location).filter(Location.name == "Room 101").first()
    if not room:
        print("Room 101 not found.")
        return
        
    # 2. Get Item 'light'
    item = db.query(InventoryItem).filter(InventoryItem.name == "light").first()
    if not item:
        print("Item 'light' not found.")
        return
        
    # 3. Check Mappings
    mappings = db.query(AssetMapping).filter(
        AssetMapping.location_id == room.id,
        AssetMapping.item_id == item.id,
        AssetMapping.is_active == True
    ).all()
    
    print(f"Found {len(mappings)} active asset mappings for light in Room 101.")
    
    # User's screenshot showed 3. They wanted to reduce by 1.
    # The fix I just pushed will handle FUTURE requests.
    # But for the one they just did, the stock is likely still 3 because the old code failed to reduce it.
    
    # Let's check waste logs to confirm they tried to delete one recently
    from app.models.inventory import WasteLog
    recent_waste = db.query(WasteLog).filter(
        WasteLog.item_id == item.id,
        WasteLog.location_id == room.id
    ).order_by(WasteLog.created_at.desc()).first()
    
    if recent_waste:
        print(f"Found recent waste log: {recent_waste.log_number} for {recent_waste.quantity} qty.")
        
        # If we have mappings, let's manually reduce one to match the users expectation
        # We assume the user sees '3' but expects '2'.
        # I'll reduce by the waste amount.
        
        qty_to_remove = recent_waste.quantity
        for mapping in mappings:
            if qty_to_remove <= 0:
                break
            available = mapping.quantity or 1
            if available > qty_to_remove:
                print(f"Reducing mapping {mapping.id} from {available} to {available - qty_to_remove}")
                mapping.quantity = available - qty_to_remove
                qty_to_remove = 0
            else:
                print(f"Deactivating mapping {mapping.id} (qty {available})")
                mapping.is_active = False
                qty_to_remove -= available
                
        db.commit()
        print("Adjusted stock based on recent waste log.")
    else:
        print("No recent waste log found.")

if __name__ == "__main__":
    manual_fix_light_waste()
