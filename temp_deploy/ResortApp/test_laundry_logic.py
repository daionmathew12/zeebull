import sys
import os
from datetime import datetime

# Add root directory to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.inventory import InventoryItem, Location, InventoryTransaction
from app.models.service import Service, AssignedService, service_inventory_item
from app.models.room import Room
from app.models.user import User

from sqlalchemy.orm import Session
from sqlalchemy import select

def setup_test_data(db: Session):
    print("--- Setting up Test Data ---")
    
    # 1. Ensure Laundry Location Exists
    laundry_loc = db.query(Location).filter(Location.location_type == "LAUNDRY").first()
    if not laundry_loc:
        print("Creating Laundry Location...")
        laundry_loc = Location(
            location_code="LOC-LNDRY-TEST",
            name="Test Laundry",
            building="Main",
            room_area="Laundry",
            location_type="LAUNDRY",
            is_inventory_point=True
        )
        db.add(laundry_loc)
        db.commit()
    print(f"Laundry Location: {laundry_loc.name} (ID: {laundry_loc.id})")

    # 2. Ensure Test Item Exists
    test_item = db.query(InventoryItem).filter(InventoryItem.name == "Test Towel").first()
    if not test_item:
        print("Creating Test Towel Item...")
        # Need a category first
        from app.models.inventory import InventoryCategory
        cat = db.query(InventoryCategory).first() 
        if not cat: 
             # Create dummy cat if none
             cat = InventoryCategory(name="Test Cat", gst_tax_rate=0, classification="Goods", hsn_sac_code="123")
             db.add(cat)
             db.commit()

        test_item = InventoryItem(
            name="Test Towel",
            category_id=cat.id,
            track_laundry_cycle=True,
            unit="pcs",
            min_stock_level=10,
            unit_price=100.0,
            gst_rate=0,
            current_stock=100.0,
            is_active=True
        )
        db.add(test_item)
        db.commit()
    else:
        # Ensure flag is on
        test_item.track_laundry_cycle = True
        db.commit()
        
    print(f"Test Item: {test_item.name} (ID: {test_item.id}) - Laundry Tracking: {test_item.track_laundry_cycle}")

    # 3. Ensure Service Exists
    test_service = db.query(Service).filter(Service.name == "Test Laundry Service").first()
    if not test_service:
        print("Creating Test Service...")
        test_service = Service(
            name="Test Laundry Service",
            charges=0,
            description="Auto generated test service"
        )
        db.add(test_service)
        db.commit()
        db.refresh(test_service)
        
        # Link Item to Service
        # ServiceInventoryItem is a table, not a mapped class usually, let's check model
        # Actually Service model usually has inventory relationship. 
        # But let's check how to insert into the association table `service_inventory_items`.
        # Assuming direct insert for simplicity if mapped object not available or using raw sql
        stmt = service_inventory_item.insert().values(
            service_id=test_service.id,
            inventory_item_id=test_item.id,
            quantity=2
        )
        db.execute(stmt)
        db.commit()
        
    print(f"Test Service: {test_service.name} (ID: {test_service.id})")

    return laundry_loc, test_item, test_service

def test_workflow():
    db = SessionLocal()
    try:
        laundry_loc, item, service = setup_test_data(db)
        
        # 4. Get a Room (or create dummy)
        room = db.query(Room).first()
        if not room:
            print("No rooms found. Creating dummy room.")
            room = Room(number="999", type="Single", floor="1", status="vacant", price=1000)
            db.add(room)
            db.commit()
            
        print(f"Using Room: {room.number}")
        
        # 5. Assign Service
        print("\n--- Executing Workflow ---")
        assigned = AssignedService(
            service_id=service.id,
            room_id=room.id,
            status="pending"
        )
        db.add(assigned)
        db.commit()
        db.refresh(assigned)
        print(f"Service Assigned (ID: {assigned.id}). Status: {assigned.status}")
        
        # 6. Mark Completed (Trigger Logic)
        print("Marking Service as COMPLETED...")
        
        # We need to trigger the logic that is in `update_assigned_service_status`.
        # Since we can't easily import that function without potential circular imports or setup issues,
        # I will simulate the update call or assume the user wants me to call the CRUD function.
        # Let's try to import the crud function.
        from app.curd.service import update_assigned_service_status
        from app.schemas.service import AssignedServiceUpdate
        
        update_data = AssignedServiceUpdate(status="completed")
        update_assigned_service_status(db, assigned.id, update_data)
        
        db.commit() # Ensure commits from function are saved
        
        # 7. Verify
        print("\n--- Verifying Results ---")
        
        # Check Transaction
        txn = db.query(InventoryTransaction).filter(
            InventoryTransaction.reference_number == f"LNDRY-COL-{assigned.id}"
        ).first()
        
        if txn:
            print(f"✓ SUCCESSS: Transaction Created!")
            print(f"  Note: {txn.notes}")
            print(f"  Qty: {txn.quantity}")
            print(f"  Type: {txn.transaction_type}")
        else:
            print("✗ FAILURE: No Transaction found with expected reference number.")
            
    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_workflow()
