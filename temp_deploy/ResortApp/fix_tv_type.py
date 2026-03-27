from app.database import SessionLocal
from app.models.inventory import InventoryItem

db = SessionLocal()

def fix_tv_type():
    print("--- Fixing Item Type for TV ---")
    
    # search for TV (case insensitive)
    tv_item = db.query(InventoryItem).filter(InventoryItem.name.ilike("TV")).first()
    
    if tv_item:
        print(f"Found Item: {tv_item.name} (ID: {tv_item.id})")
        print(f"Current Status: {'Asset' if tv_item.is_asset_fixed else 'Consumable'}")
        
        if not tv_item.is_asset_fixed:
            tv_item.is_asset_fixed = True
            db.commit()
            print("Updated to: Asset")
        else:
            print("Already an Asset.")
    else:
        print("Item 'TV' not found.")
        
    print("--- Check Complete ---")

if __name__ == "__main__":
    fix_tv_type()
