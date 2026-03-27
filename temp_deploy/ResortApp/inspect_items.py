from app.database import SessionLocal
from app.models.inventory import InventoryItem, InventoryCategory

db = SessionLocal()

items = db.query(InventoryItem).filter(InventoryItem.name.in_(["Coca Cola", "Mineral Water", "Smart TV 43 Inch", "Electric Kettle"])).all()

print(f"{'Name':<20} | {'Is Fixed Ass':<12} | {'Sellable':<8} | {'Perishable':<10} | {'Laundry':<8} | {'Category':<15} | {'Cat Fixed':<10}")
print("-" * 100)

for item in items:
    cat = db.query(InventoryCategory).filter(InventoryCategory.id == item.category_id).first()
    cat_fixed = cat.is_asset_fixed if cat else "N/A"
    cat_name = cat.name if cat else "None"
    
    print(f"{item.name:<20} | {str(item.is_asset_fixed):<12} | {str(item.is_sellable_to_guest):<8} | {str(item.is_perishable):<10} | {str(item.track_laundry_cycle):<8} | {cat_name:<15} | {str(cat_fixed):<10}")

db.close()
