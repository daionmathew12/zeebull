from app.database import SessionLocal
from app.models.inventory import InventoryItem
import json

def check_items():
    db = SessionLocal()
    items = db.query(InventoryItem).filter(
        (InventoryItem.name.ilike('%LED Bulb%')) | (InventoryItem.name.ilike('%Bath towel%')) | (InventoryItem.name.ilike('%TV%'))
    ).all()
    
    result = []
    for item in items:
        result.append({
            "id": item.id,
            "name": item.name,
            "unit_price": item.unit_price,
            "gst_rate": item.gst_rate,
            "selling_price": item.selling_price,
            "is_asset_fixed": item.is_asset_fixed,
            "complimentary_limit": item.complimentary_limit
        })
    print(json.dumps(result, indent=2))
    db.close()

if __name__ == "__main__":
    check_items()
