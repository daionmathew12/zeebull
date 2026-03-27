from app.database import SessionLocal
from app.models.inventory import InventoryItem, InventoryCategory

db = SessionLocal()

items = db.query(InventoryItem).all()

print(f"{'Name':<30} | {'Is Fixed':<8} | {'Cat Fixed':<8} | {'Laundry':<8} | {'Sellable':<8} | {'Perish':<8} | {'Heuristic'}")
print("-" * 110)

for item in items:
    cat = db.query(InventoryCategory).filter(InventoryCategory.id == item.category_id).first()
    is_fixed = item.is_asset_fixed
    cat_fixed = cat.is_asset_fixed if cat else False
    laundry = item.track_laundry_cycle
    sellable = item.is_sellable_to_guest
    perishable = item.is_perishable
    
    heuristic = (not sellable and not perishable)
    is_asset_explicit = (is_fixed or cat_fixed or laundry)
    
    if heuristic and not is_asset_explicit:
         print(f"{item.name[:30]:<30} | {str(is_fixed):<8} | {str(cat_fixed):<8} | {str(laundry):<8} | {str(sellable):<8} | {str(perishable):<8} | {str(heuristic)}")

db.close()
