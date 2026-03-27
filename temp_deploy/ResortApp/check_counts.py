from app.database import SessionLocal
from app.models.inventory import LocationStock, AssetMapping, InventoryItem, AssetRegistry

def check_db():
    db = SessionLocal()
    loc_id = 5 # Room 102
    
    print(f"--- LocationStock (Loc {loc_id}) ---")
    stocks = db.query(LocationStock).filter(LocationStock.location_id == loc_id).all()
    for s in stocks:
        item = db.query(InventoryItem).filter(InventoryItem.id == s.item_id).first()
        print(f"Item: {item.name if item else s.item_id}, Qty: {s.quantity}")
        
    print(f"\n--- AssetMapping (Loc {loc_id}) ---")
    mappings = db.query(AssetMapping).filter(AssetMapping.location_id == loc_id, AssetMapping.is_active == True).all()
    for m in mappings:
        item = db.query(InventoryItem).filter(InventoryItem.id == m.item_id).first()
        print(f"Item: {item.name if item else m.item_id}, Qty: {m.quantity}")

    print(f"\n--- AssetRegistry (Loc {loc_id}) ---")
    registry = db.query(AssetRegistry).filter(AssetRegistry.current_location_id == loc_id).all()
    for a in registry:
        item = db.query(InventoryItem).filter(InventoryItem.id == a.item_id).first()
        print(f"ID: {a.id}, Item: {item.name if item else a.item_id}, Code: {a.asset_code}")
        
    db.close()

if __name__ == "__main__":
    check_db()
