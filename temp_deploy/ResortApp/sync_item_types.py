from app.database import SessionLocal
from app.models.inventory import InventoryItem, InventoryCategory

db = SessionLocal()

def sync_item_types_with_category():
    print("--- Syncing Item Types with Category Defaults ---")
    
    # Fetch all categories into a map
    categories = db.query(InventoryCategory).all()
    cat_map = {c.id: c.is_asset_fixed for c in categories}
    cat_name_map = {c.id: c.name for c in categories}
    
    items = db.query(InventoryItem).filter(InventoryItem.is_active == True).all()
    
    updated_count = 0
    
    for item in items:
        if item.category_id in cat_map:
            expected_type = cat_map[item.category_id]
            current_type = item.is_asset_fixed
            
            if current_type != expected_type:
                print(f"Updating Item '{item.name}' (Cat: {cat_name_map[item.category_id]}) -> {'Asset' if expected_type else 'Consumable'}")
                item.is_asset_fixed = expected_type
                updated_count += 1
        else:
            print(f"Warning: Item '{item.name}' has invalid category ID {item.category_id}")

    if updated_count > 0:
        db.commit()
    
    print(f"--- Completed. Updated {updated_count} items. ---")

if __name__ == "__main__":
    sync_item_types_with_category()
