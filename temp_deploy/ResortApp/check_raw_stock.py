from app.database import SessionLocal
from app.models.inventory import LocationStock, AssetMapping, InventoryItem

def check_raw():
    db = SessionLocal()
    loc_id = 6 # Room 103
    
    print("--- LocationStock (Room 103) ---")
    stk = db.query(LocationStock).filter(LocationStock.location_id == loc_id).all()
    for s in stk:
        print(f"ID:{s.item_id} | Name:{s.item.name} | Qty:{s.quantity}")
        
    print("\n--- AssetMapping (Room 103) ---")
    map = db.query(AssetMapping).filter(AssetMapping.location_id == loc_id, AssetMapping.is_active == True).all()
    for m in map:
        print(f"ID:{m.item_id} | Name:{m.item.name} | Qty:{m.quantity}")
        
    db.close()

if __name__ == "__main__":
    check_raw()
