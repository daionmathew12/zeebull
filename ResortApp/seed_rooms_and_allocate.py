
import sys
import os
import random
from datetime import timezone, datetime

# Add current directory to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.inventory import Location, InventoryItem, LocationStock, StockIssue, StockIssueDetail, User
from app.models.inventory import Vendor # Just in case

def seed_rooms_and_allocate():
    db = SessionLocal()
    try:
        print("Starting Room Seeding & Allocation...")
        
        # 1. Get Admin User for 'issued_by'
        admin = db.query(User).filter(User.email == "admin@orchid.com").first()
        admin_id = admin.id if admin else 1

        # 2. Get Main Warehouse
        warehouse = db.query(Location).filter(Location.location_type == "WAREHOUSE").first()
        if not warehouse:
            print("Error: Main Warehouse not found. Please run seed_inventory_items.py first.")
            return

        # 3. Create Rooms
        rooms_data = [
            {"name": "Room 101", "building": "Main Block", "floor": "1st Floor"},
            {"name": "Room 102", "building": "Main Block", "floor": "1st Floor"},
            {"name": "Room 103", "building": "Main Block", "floor": "1st Floor"},
            {"name": "Room 104", "building": "Main Block", "floor": "1st Floor"},
            {"name": "Room 105", "building": "Main Block", "floor": "1st Floor"},
        ]
        
        created_rooms = []
        for r_data in rooms_data:
            room = db.query(Location).filter(Location.name == r_data["name"]).first()
            if not room:
                room = Location(
                    name=r_data["name"],
                    building=r_data["building"],
                    floor=r_data["floor"],
                    room_area=r_data["name"], # mapping name to room_area
                    location_type="GUEST_ROOM",
                    is_inventory_point=True, # Rooms hold stock (minibar, linen)
                    description="Standard Guest Room"
                )
                db.add(room)
                db.commit()
                db.refresh(room)
                print(f"Created Location: {room.name}")
            created_rooms.append(room)

        # 4. Identify Items to Allocate (Standard Setup)
        # Using partial matching or exact names from seed_inventory_items.py
        items_to_allocate = [
            {"name": "Bed Sheet (King)", "qty": 1},
            {"name": "Pillow Cover", "qty": 2},
            {"name": "Bath Towel (White)", "qty": 2},
            {"name": "Hand Towel", "qty": 2},
            {"name": "Soap Bar (Small)", "qty": 2},
            {"name": "Shampoo Bottle (30ml)", "qty": 2},
            {"name": "Mineral Water (1L)", "qty": 2}
        ]
        
        resolved_items = []
        for item_def in items_to_allocate:
            item = db.query(InventoryItem).filter(InventoryItem.name == item_def["name"]).first()
            if item:
                resolved_items.append({
                    "item": item,
                    "qty": item_def["qty"]
                })
            else:
                print(f"Warning: Item '{item_def['name']}' not found. Skipping.")

        # 5. Issue Stock to Rooms
        for room in created_rooms:
            print(f"\nAllocating items to {room.name}...")
            
            # Create Stock Issue Header
            issue = StockIssue(
                issue_number=f"ISS-RM-{room.id}-{random.randint(1000,9999)}",
                issued_by=admin_id,
                source_location_id=warehouse.id,
                destination_location_id=room.id,
                issue_date=datetime.now(timezone.utc),
                notes="Initial Room Setup / Allocation"
            )
            db.add(issue)
            db.flush() # Get ID
            
            for alloc in resolved_items:
                item = alloc["item"]
                qty = alloc["qty"]
                
                # Check Warehouse Stock
                wh_stock = db.query(LocationStock).filter(
                    LocationStock.location_id == warehouse.id,
                    LocationStock.item_id == item.id
                ).first()
                
                if wh_stock and wh_stock.quantity >= qty:
                    # Deduct from Warehouse
                    wh_stock.quantity -= qty
                    
                    # Add to Room
                    room_stock = db.query(LocationStock).filter(
                        LocationStock.location_id == room.id,
                        LocationStock.item_id == item.id
                    ).first()
                    
                    if room_stock:
                        room_stock.quantity += qty
                    else:
                        room_stock = LocationStock(
                            location_id=room.id,
                            item_id=item.id,
                            quantity=qty,
                            last_updated=datetime.now(timezone.utc)
                        )
                        db.add(room_stock)
                        
                    # Create Issue Detail
                    detail = StockIssueDetail(
                        issue_id=issue.id,
                        item_id=item.id,
                        issued_quantity=qty,
                        unit=item.unit,
                        unit_price=item.unit_price,
                        cost=qty * item.unit_price,
                        notes="Standard Setup"
                    )
                    db.add(detail)
                    print(f"  - Issued {qty} {item.unit} of {item.name}")
                else:
                    print(f"  X Insufficient stock for {item.name} in Warehouse")
            
            db.commit()
            
        print("\nRoom Allocation Completed Successfully!")

    except Exception as e:
        print(f"Error Allocating to Rooms: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_rooms_and_allocate()
