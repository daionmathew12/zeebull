from app.database import SessionLocal
from app.models.inventory import LocationStock, AssetMapping, Location
from app.models.booking import Room

def check_stock_103():
    db = SessionLocal()
    room = db.query(Room).filter(Room.number == "103").first()
    if not room:
        print("Room 103 not found")
        return
        
    loc_id = room.inventory_location_id
    print(f"Room 103 Location ID: {loc_id}")
    
    # Check LocationStock
    stocks = db.query(LocationStock).filter(LocationStock.location_id == loc_id).all()
    print("\n--- Location Stock ---")
    for s in stocks:
        print(f"Item ID {s.item_id}: {s.item.name} | Qty: {s.quantity}")
        
    # Check AssetMapping
    mappings = db.query(AssetMapping).filter(AssetMapping.location_id == loc_id, AssetMapping.is_active == True).all()
    print("\n--- Asset Mappings (Permanent) ---")
    for m in mappings:
        print(f"Item ID {m.item_id}: {m.item.name} | Qty: {m.quantity}")
        
    db.close()

if __name__ == "__main__":
    check_stock_103()
