
import sys
import os
import random
from datetime import timezone, datetime

# Add current directory to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.inventory import Location, InventoryItem, LocationStock, StockIssue, StockIssueDetail, InventoryCategory
from app.models.user import User
from sqlalchemy.orm import Session

def seed_diverse_rooms_and_allocate():
    db = SessionLocal()
    try:
        print("Starting Diverse Room Seeding & Allocation...")
        
        # 1. Get Admin User for 'issued_by'
        admin = db.query(User).filter(User.email == "admin@orchid.com").first()
        admin_id = admin.id if admin else 1

        # 2. Get Main Warehouse
        warehouse = db.query(Location).filter(Location.location_type == "WAREHOUSE").first()
        if not warehouse:
            print("Error: Main Warehouse not found.")
            return

        # 3. Define Room Categories/Types and their specific Locations
        room_categories = [
            {"type": "Standard Room", "prefix": "10", "count": 5},        # 101-105
            {"type": "Deluxe Room", "prefix": "20", "count": 5},          # 201-205
            {"type": "Suite", "prefix": "30", "count": 5},                # 301-305
            {"type": "Executive Suite", "prefix": "40", "count": 5},      # 401-405
            {"type": "Presidential Suite", "prefix": "50", "count": 5}    # 501-505
        ]

        # 4. Define Allocation Templates based on Room Type
        # Ensure these items exist in seed_inventory_items.py
        allocations = {
            "Standard Room": [
                {"name": "Bed Sheet (King)", "qty": 1},
                {"name": "Pillow Cover", "qty": 2},
                {"name": "Bath Towel (White)", "qty": 2},
                {"name": "Soap Bar (Small)", "qty": 2},
                {"name": "Mineral Water (1L)", "qty": 2}
            ],
            "Deluxe Room": [
                {"name": "Bed Sheet (King)", "qty": 1},
                {"name": "Pillow Cover", "qty": 4},
                {"name": "Bath Towel (White)", "qty": 2},
                {"name": "Hand Towel", "qty": 2},
                {"name": "Soap Bar (Small)", "qty": 2},
                {"name": "Shampoo Bottle (30ml)", "qty": 2},
                {"name": "Mineral Water (1L)", "qty": 3},
                {"name": "Coffee Beans", "qty": 0.1} # 100g
            ],
            "Suite": [
                {"name": "Bed Sheet (King)", "qty": 2},
                {"name": "Pillow Cover", "qty": 6},
                {"name": "Bath Towel (White)", "qty": 4},
                {"name": "Hand Towel", "qty": 4},
                {"name": "Bath Robe", "qty": 2},
                {"name": "Soap Bar (Small)", "qty": 4},
                {"name": "Shampoo Bottle (30ml)", "qty": 4},
                {"name": "Toothpaste Kit", "qty": 2},
                {"name": "Mineral Water (1L)", "qty": 4},
                {"name": "Fruit Juice (1L)", "qty": 1},
                {"name": "Soda Cans", "qty": 2}
            ],
            "Executive Suite": [
                {"name": "Bed Sheet (King)", "qty": 2},
                {"name": "Pillow Cover", "qty": 6},
                {"name": "Bath Towel (White)", "qty": 4},
                {"name": "Hand Towel", "qty": 4},
                {"name": "Bath Robe", "qty": 2},
                {"name": "Soap Bar (Small)", "qty": 4},
                {"name": "Shampoo Bottle (30ml)", "qty": 4},
                {"name": "Toothpaste Kit", "qty": 4},
                {"name": "Mineral Water (1L)", "qty": 6},
                {"name": "Fruit Juice (1L)", "qty": 2},
                {"name": "Soda Cans", "qty": 4},
                {"name": "Coffee Beans", "qty": 0.2}
            ],
            "Presidential Suite": [
                {"name": "Bed Sheet (King)", "qty": 3},
                {"name": "Pillow Cover", "qty": 8},
                {"name": "Bath Towel (White)", "qty": 6},
                {"name": "Hand Towel", "qty": 6},
                {"name": "Bath Robe", "qty": 4},
                {"name": "Soap Bar (Small)", "qty": 6},
                {"name": "Shampoo Bottle (30ml)", "qty": 6},
                {"name": "Toothpaste Kit", "qty": 6},
                {"name": "Mineral Water (1L)", "qty": 10},
                {"name": "Fruit Juice (1L)", "qty": 4},
                {"name": "Soda Cans", "qty": 6},
                {"name": "Coffee Beans", "qty": 0.5},
                {"name": "Notepads", "qty": 2},
                {"name": "Ballpoint Pen (Blue)", "qty": 2}
            ]
        }

        # 5. Process Each Category
        for cat in room_categories:
            print(f"\nProcessing {cat['type']}s...")
            
            # Create 5 Rooms for this category
            for i in range(1, cat["count"] + 1):
                room_num = f"{cat['prefix']}{i}"
                room_name = f"Room {room_num}"
                
                # Create/Get Location
                room = db.query(Location).filter(Location.name == room_name).first()
                if not room:
                    room = Location(
                        name=room_name,
                        building="Main Block",
                        floor=f"{cat['prefix'][0]}th Floor", # rough logic for floor
                        room_area=cat['type'],
                        location_type="GUEST_ROOM",
                        is_inventory_point=True,
                        description=f"{cat['type']} - {room_name}"
                    )
                    db.add(room)
                    db.commit()
                    db.refresh(room)
                    print(f"  Created Location: {room.name}")
                
                # Issue Stock
                issue_items = allocations.get(cat["type"], [])
                
                # Determine items to physically issue
                items_to_issue = []
                for item_def in issue_items:
                    item = db.query(InventoryItem).filter(InventoryItem.name == item_def["name"]).first()
                    if item:
                        items_to_issue.append({"item": item, "qty": item_def["qty"]})

                if items_to_issue:
                    # Create Stock Issue Header
                    issue = StockIssue(
                        issue_number=f"ISS-{room_num}-{random.randint(1000,9999)}",
                        issued_by=admin_id,
                        source_location_id=warehouse.id,
                        destination_location_id=room.id,
                        issue_date=datetime.now(timezone.utc),
                        notes=f"Initial Setup for {cat['type']}"
                    )
                    db.add(issue)
                    db.flush()

                    for alloc in items_to_issue:
                        item = alloc["item"]
                        qty = alloc["qty"]

                        # Check Warehouse Stock
                        wh_stock = db.query(LocationStock).filter(
                            LocationStock.location_id == warehouse.id,
                            LocationStock.item_id == item.id
                        ).first()

                        if wh_stock: # Allow negative stock for seeding if needed, or check qty
                             # Deduct from Warehouse (simple logic, assuming infinite warehouse for seeding sake if we want, but let's try to be real)
                            if wh_stock.quantity >= qty:
                                wh_stock.quantity -= qty
                            else:
                                # Auto-replenish warehouse for seeding script to not fail
                                wh_stock.quantity += 100 
                                wh_stock.quantity -= qty
                                print(f"    (Auto-replenished {item.name} in warehouse)")

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
                            
                            # Create Detail
                            detail = StockIssueDetail(
                                issue_id=issue.id,
                                item_id=item.id,
                                issued_quantity=qty,
                                unit=item.unit,
                                unit_price=item.unit_price,
                                cost=qty * item.unit_price,
                                notes="Seeding"
                            )
                            db.add(detail)
                    
                    db.commit()
                    print(f"  Allocated stock to {room.name}")

        print("\nDiverse Room Seeding Completed Successfully!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_diverse_rooms_and_allocate()
