import sys
import os
import random
from datetime import date, datetime, timedelta

# Add parent directory to path to import app modules
sys.path.append(os.getcwd())

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, SessionLocal
from app.models.booking import Booking, BookingRoom
from app.models.room import Room
from app.models.checkout import Checkout, CheckoutRequest
from app.models.inventory import InventoryItem, Location, LocationStock, StockIssue, StockIssueDetail, InventoryCategory
from app.curd.inventory import create_stock_issue
from app.schemas.inventory import StockIssueCreate, StockIssueDetailCreate
from app.api.checkout import create_checkout_request, process_booking_checkout
from app.schemas.checkout import CheckoutRequest as CheckoutRequestSchema, RoomVerificationData, ConsumableAuditItem

def setup_test_data(db):
    print("Setting up test data...")
    
    # 1. Create Test Room
    # Use a simple numeric string to avoid parsing errors if logic expects int-like
    room_number = "101" 
    
    # Create Room Location first
    room_location = Location(
        name=f"Location for {room_number}",
        location_type="Guest Room",
        description="Test Room Location"
    )
    db.add(room_location)
    db.commit()
    
    # Check if room exists
    existing_room = db.query(Room).filter(Room.number == room_number).first()
    if existing_room:
        print(f"Room {room_number} exists, reusing...")
        room = existing_room
        # Update inventory location if needed
        room.inventory_location_id = room_location.id
        db.commit()
    else:
        room = Room(
            number=room_number,
            type="Suite", 
            status="Occupied",
            price=1000.0,
            inventory_location_id=room_location.id
        )
        db.add(room)
        db.commit()
    
    print(f"Created/Found Room: {room.number} with Location ID: {room_location.id}")
    
    # 2. Create Warehouse Location
    warehouse = db.query(Location).filter(Location.location_type == "Warehouse").first()
    if not warehouse:
        warehouse = Location(
            name="Main Warehouse",
            location_type="Warehouse",
            description="Main Warehouse"
        )
        db.add(warehouse)
        db.commit()
    print(f"Warehouse ID: {warehouse.id}")
    
    # 3. Create Inventory Item
    cat = db.query(InventoryCategory).first()
    if not cat:
        cat = InventoryCategory(name="Test Cat", classification="Consumable")
        db.add(cat)
        db.commit()
        
    item = InventoryItem(
        name=f"Test Cola {random.randint(100,999)}",
        category_id=cat.id,
        current_stock=100.0,
        min_stock_level=10.0,
        unit="pcs",
        unit_price=20.0,
        selling_price=50.0,
        is_sellable_to_guest=True,
        complimentary_limit=0
    )
    db.add(item)
    db.commit()
    print(f"Created Item: {item.name}, ID: {item.id}, Global Stock: {item.current_stock}")
    
    # 4. Issue Item to Room
    # Create Stock Issue schema
    # Manually issue
    stock_issue = StockIssue(
        source_location_id=warehouse.id,
        destination_location_id=room_location.id,
        issue_date=datetime.now(),
        status="approved",
        issued_by_id=None
    )
    db.add(stock_issue)
    db.commit()
    
    issue_detail = StockIssueDetail(
        issue_id=stock_issue.id,
        item_id=item.id,
        quantity=10.0
    )
    db.add(issue_detail)
    
    # Update Stocks manually as `create_stock_issue` would
    # Decrease Warehouse
    item.current_stock -= 10.0
    
    # Increase Room Location Stock
    loc_stock = db.query(LocationStock).filter(
        LocationStock.location_id == room_location.id, 
        LocationStock.item_id == item.id
    ).first()
    if not loc_stock:
        loc_stock = LocationStock(
            location_id=room_location.id,
            item_id=item.id,
            quantity=0.0
        )
        db.add(loc_stock)
    loc_stock.quantity += 10.0
    
    db.commit()
    db.refresh(item)
    db.refresh(loc_stock)
    
    print(f"After Issue -> Global Stock: {item.current_stock}, Room Stock: {loc_stock.quantity}")
    
    # 5. Create Booking
    booking = Booking(
        guest_name="Test Guest",
        check_in=date.today(),
        check_out=date.today() + timedelta(days=1),
        status="checked-in",
        room_count=1,
        number_of_guests=1,
        total_amount=1000.0
    )
    db.add(booking)
    db.commit()
    
    booking_room = BookingRoom(
        booking_id=booking.id,
        room_id=room.id,
        price=1000.0,
        occupancy=1
    )
    db.add(booking_room)
    db.commit()
    
    return room, booking, item, loc_stock

def test_checkout_return(db):
    try:
        room, booking, item, loc_stock_start = setup_test_data(db)
        
        # Verify pre-checkout state
        initial_global_stock = item.current_stock
        initial_room_stock = loc_stock_start.quantity
        print(f"Pre-Checkout: Global={initial_global_stock}, Room={initial_room_stock}")
        
        # Mock Checkout Request creation (DB level)
        checkout_req = CheckoutRequest(
            booking_id=booking.id,
            room_number=room.number,
            status="completed",
            inventory_data=[{
                "item_id": item.id,
                "used_qty": 1.0, # Consumed 1
                "missing_qty": 0.0,
                "item_name": item.name
            }] 
        )
        db.add(checkout_req)
        db.commit()
        
        # Pydantic Request
        req_pydantic = CheckoutRequestSchema(
            checkout_mode="single",
            payment_method="cash",
            room_verifications=[
                RoomVerificationData(
                    room_number=room.number,
                    consumables=[
                        ConsumableAuditItem(
                            item_id=item.id,
                            item_name=item.name,
                            actual_consumed=1.0, # Frontend sends verified consumed amount
                            complimentary_limit=0,
                            charge_per_unit=item.selling_price,
                            total_charge=item.selling_price
                        )
                    ],
                    asset_damages=[]
                )
            ]
        )
        
        # Mock User
        class MockUser:
            id = 1
            name = "Test Admin"
            
        print("Processing Checkout...")
        result = process_booking_checkout(room.number, req_pydantic, db, MockUser())
        
        print(f"Checkout Completed. Bill ID: {result.checkout_id}")
        
        # Check Stocks
        db.refresh(item)
        db.refresh(loc_stock_start) # Reload room stock
        
        final_global_stock = item.current_stock
        final_room_stock = loc_stock_start.quantity
        
        print(f"Post-Checkout: Global={final_global_stock}, Room={final_room_stock}")
        
        # Assertions
        
        # 1. Global Stock Check
        status_global = "Unknown"
        if final_global_stock == initial_global_stock:
            status_global = "Passed"
            print("SUCCESS: Global Stock preserved.")
        else:
            status_global = "Failed"
            print(f"FAILURE: Global Stock changed! {initial_global_stock} -> {final_global_stock}")
            
        # 2. Room Stock Check
        status_room = "Unknown"
        if final_room_stock == (initial_room_stock - 1):
             status_room = "Passed"
             print("SUCCESS: Room Stock decremented correctly.")
        else:
             status_room = "Failed"
             print(f"FAILURE: Room Stock incorrect! Expected {initial_room_stock - 1}, Got {final_room_stock}")
        
        return {
            "Global Stock": status_global,
            "Room Stock": status_room,
            "Details": f"Global: {initial_global_stock}->{final_global_stock}, Room: {initial_room_stock}->{final_room_stock}"
        }
        
    except Exception as e:
        print(f"Test Failed with Exception: {e}")
        import traceback
        traceback.print_exc()
        return {"Error": str(e)}

if __name__ == "__main__":
    db = SessionLocal()
    test_checkout_return(db)
