"""
Test asset mapping creation with the fixed code
"""
from app.database import SessionLocal
from app.curd import inventory as inventory_crud
from app.models.inventory import Location, InventoryItem

def test_asset_mapping():
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("TESTING ASSET MAPPING CREATION")
        print("=" * 70)
        
        # 1. Find the warehouse
        warehouse = db.query(Location).filter(
            Location.location_type.in_(["WAREHOUSE", "CENTRAL_WAREHOUSE", "Warehouse"])
        ).first()
        
        if warehouse:
            print(f"\n✅ Found warehouse: {warehouse.building} - {warehouse.room_area} (ID: {warehouse.id})")
        else:
            print("\n❌ No warehouse found!")
            return
        
        # 2. Find Room 102
        room_102 = db.query(Location).filter(
            Location.room_area.ilike("%102%")
        ).first()
        
        if room_102:
            print(f"✅ Found Room 102: {room_102.building} - {room_102.room_area} (ID: {room_102.id})")
        else:
            print("❌ Room 102 not found!")
            return
        
        # 3. Find LED TV item
        led_tv = db.query(InventoryItem).filter(
            InventoryItem.name.ilike("%LED TV%")
        ).first()
        
        if led_tv:
            print(f"✅ Found LED TV: {led_tv.name} (ID: {led_tv.id}, Stock: {led_tv.current_stock})")
        else:
            print("❌ LED TV not found!")
            return
        
        # 4. Try to create asset mapping
        print("\n" + "=" * 70)
        print("CREATING ASSET MAPPING")
        print("=" * 70)
        
        data = {
            "item_id": led_tv.id,
            "location_id": room_102.id,
            "serial_number": "TEST12345",
            "quantity": 1.0,
            "notes": "Test asset mapping"
        }
        
        print(f"\nData: {data}")
        
        # This will test if the warehouse lookup works
        result = inventory_crud.create_asset_mapping(db, data, assigned_by=1)
        
        print(f"\n✅ SUCCESS! Asset mapping created with ID: {result.id}")
        
        # Rollback to not actually create it
        db.rollback()
        print("\n(Rolled back - this was just a test)")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_asset_mapping()
