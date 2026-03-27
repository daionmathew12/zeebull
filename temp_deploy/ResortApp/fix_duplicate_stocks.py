"""
Fix Duplicate LocationStock Records
Merges duplicate LocationStock records for the same item at the same location.
"""
from app.database import SessionLocal
from app.models.inventory import LocationStock
from sqlalchemy import func

def fix_duplicate_location_stocks():
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("FIXING DUPLICATE LOCATION STOCK RECORDS")
        print("=" * 70)
        
        # Find duplicates: same location_id + item_id with multiple records
        duplicates = db.query(
            LocationStock.location_id,
            LocationStock.item_id,
            func.count(LocationStock.id).label('count'),
            func.sum(LocationStock.quantity).label('total_qty')
        ).group_by(
            LocationStock.location_id,
            LocationStock.item_id
        ).having(
            func.count(LocationStock.id) > 1
        ).all()
        
        if not duplicates:
            print("\n✅ No duplicate records found!")
            return
        
        print(f"\nFound {len(duplicates)} duplicate groups:")
        
        fixed_count = 0
        for dup in duplicates:
            location_id, item_id, count, total_qty = dup
            
            # Get all records for this location + item
            records = db.query(LocationStock).filter(
                LocationStock.location_id == location_id,
                LocationStock.item_id == item_id
            ).order_by(LocationStock.id).all()
            
            if len(records) <= 1:
                continue
            
            # Get item and location names for display
            from app.models.inventory import InventoryItem, Location
            item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
            location = db.query(Location).filter(Location.id == location_id).first()
            
            item_name = item.name if item else f"Item #{item_id}"
            location_name = location.name if location else f"Location #{location_id}"
            
            print(f"\n📦 {item_name} at {location_name}:")
            print(f"   Found {len(records)} duplicate records:")
            for r in records:
                print(f"   - ID: {r.id}, Qty: {r.quantity}, Updated: {r.last_updated}")
            
            # Keep the first record, merge quantities, delete others
            primary_record = records[0]
            total_quantity = sum(r.quantity for r in records)
            
            print(f"   Merging into record ID {primary_record.id}")
            print(f"   Total quantity: {total_quantity}")
            
            # Update primary record with total quantity
            primary_record.quantity = total_quantity
            
            # Delete duplicate records
            for record in records[1:]:
                print(f"   Deleting duplicate record ID {record.id}")
                db.delete(record)
            
            fixed_count += 1
        
        db.commit()
        
        print("\n" + "=" * 70)
        print(f"✅ FIXED {fixed_count} DUPLICATE GROUPS!")
        print("=" * 70)
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    fix_duplicate_location_stocks()
