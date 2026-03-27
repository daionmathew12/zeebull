from app.database import SessionLocal
from app.models.inventory import LocationStock
from sqlalchemy import func

db = SessionLocal()

def fix_duplicates():
    print("Checking for duplicate LocationStock entries...")
    
    # Find duplicates
    duplicates = db.query(
        LocationStock.location_id,
        LocationStock.item_id,
        func.count(LocationStock.id).label('cnt')
    ).group_by(
        LocationStock.location_id,
        LocationStock.item_id
    ).having(func.count(LocationStock.id) > 1).all()

    if not duplicates:
        print("No duplicates found.")
        return

    print(f"Found {len(duplicates)} sets of duplicates.")

    for loc_id, item_id, count in duplicates:
        print(f"Processing Loc {loc_id}, Item {item_id} (Count: {count})")
        
        records = db.query(LocationStock).filter(
            LocationStock.location_id == loc_id,
            LocationStock.item_id == item_id
        ).all()
        
        # Merge
        total_qty = sum(float(r.quantity) for r in records)
        first = records[0]
        others = records[1:]
        
        print(f"  Mergin {len(records)} records. Total Qty: {total_qty}")
        
        first.quantity = total_qty
        
        for o in others:
            db.delete(o)
            
        db.commit()
        print("  Merged successfully.")

if __name__ == "__main__":
    fix_duplicates()
