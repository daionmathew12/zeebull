from app.database import SessionLocal
from app.models.inventory import InventoryItem
from sqlalchemy.orm import joinedload
import json

def debug():
    db = SessionLocal()
    items = db.query(InventoryItem).options(joinedload(InventoryItem.category)).filter(
        (InventoryItem.name.ilike('%Bath towel%')) | 
        (InventoryItem.name.ilike('%Coca%')) | 
        (InventoryItem.name.ilike('%TV%'))
    ).all()
    
    out = []
    for i in items:
        out.append({
            "name": i.name,
            "category": i.category.name if i.category else None,
            "selling_price": float(i.selling_price or 0.0),
            "unit_price": float(i.unit_price or 0.0),
            "is_fixed": i.is_asset_fixed,
            "sellable": getattr(i, 'is_sellable_to_guest', False)
        })
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    debug()
