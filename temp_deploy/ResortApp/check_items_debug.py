from app.database import SessionLocal
from app.models.inventory import InventoryItem, InventoryCategory
from sqlalchemy.orm import joinedload
import json

def check_items():
    db = SessionLocal()
    items = db.query(InventoryItem).options(joinedload(InventoryItem.category)).filter(
        (InventoryItem.name.ilike('%LED Bulb%')) | 
        (InventoryItem.name.ilike('%Bath towel%')) | 
        (InventoryItem.name.ilike('%TV%')) |
        (InventoryItem.name.ilike('%Coca%')) |
        (InventoryItem.name.ilike('%Water%'))
    ).all()
    
    result = []
    for item in items:
        result.append({
            "id": item.id,
            "name": item.name,
            "category": item.category.name if item.category else None,
            "unit_price": item.unit_price,
            "gst_rate": item.gst_rate,
            "selling_price": item.selling_price,
            "is_asset_fixed": item.is_asset_fixed,
            "is_sellable": getattr(item, 'is_sellable_to_guest', 'N/A'),
            "complimentary_limit": item.complimentary_limit
        })
    print(json.dumps(result, indent=2))
    db.close()

if __name__ == "__main__":
    check_items()
