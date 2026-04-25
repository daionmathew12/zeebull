
import sys
import os
import random
from datetime import timezone, datetime

# Add current directory to path
sys.path.append(os.getcwd())

from app.database import SessionLocal, engine, Base
from app.models.inventory import InventoryCategory, InventoryItem, Location, LocationStock, Vendor

def seed_inventory():
    db = SessionLocal()
    try:
        print("Starting Inventory Seeding...")
        
        # 1. Ensure a Main Warehouse Location exists
        warehouse = db.query(Location).filter(Location.location_type == "WAREHOUSE").first()
        if not warehouse:
            warehouse = Location(
                name="Main Warehouse",
                building="Main Block",
                room_area="Basement",
                location_type="WAREHOUSE",
                is_inventory_point=True,
                description="Central storage for all resort items"
            )
            db.add(warehouse)
            db.commit()
            db.refresh(warehouse)
            print(f"Created Warehouse: {warehouse.name}")
        else:
            print(f"Using existing Warehouse: {warehouse.name}")

        # 2. Ensure a Default Vendor exists
        vendor = db.query(Vendor).first()
        if not vendor:
            vendor = Vendor(
                name="General Supplier",
                contact_person="John Doe",
                phone="9876543210",
                email="supplier@example.com",
                address="123 Industrial Area",
                gst_number="29ABCDE1234F1Z5"
            )
            db.add(vendor)
            db.commit()
            db.refresh(vendor)
            print(f"Created Vendor: {vendor.name}")
        else:
            print(f"Using existing Vendor: {vendor.name}")

        # 3. Define Categories and Items
        categories_data = [
            {
                "name": "Restaurant - Raw Materials",
                "department": "Restaurant",
                "items": [
                    {"name": "Basmati Rice", "unit": "kg", "price": 80.0, "min_stock": 50},
                    {"name": "Cooking Oil (Sunflower)", "unit": "liter", "price": 120.0, "min_stock": 20},
                    {"name": "Chicken Breast (Frozen)", "unit": "kg", "price": 250.0, "min_stock": 10, "is_perishable": True},
                    {"name": "Wheat Flour (Atta)", "unit": "kg", "price": 40.0, "min_stock": 30},
                    {"name": "Sugar", "unit": "kg", "price": 45.0, "min_stock": 25}
                ]
            },
            {
                "name": "Restaurant - Beverages",
                "department": "Restaurant",
                "items": [
                    {"name": "Coffee Beans", "unit": "kg", "price": 800.0, "min_stock": 5},
                    {"name": "Tea Dust", "unit": "kg", "price": 300.0, "min_stock": 5},
                    {"name": "Mineral Water (1L)", "unit": "bottle", "price": 15.0, "selling_price": 40.0, "min_stock": 100, "is_sellable": True},
                    {"name": "Soda Cans", "unit": "can", "price": 20.0, "selling_price": 60.0, "min_stock": 50, "is_sellable": True},
                    {"name": "Fruit Juice (1L)", "unit": "pack", "price": 90.0, "min_stock": 20}
                ]
            },
            {
                "name": "Housekeeping - Linen",
                "department": "Housekeeping",
                "track_laundry": True,
                "items": [
                    {"name": "Bath Towel (White)", "unit": "pcs", "price": 400.0, "min_stock": 50},
                    {"name": "Hand Towel", "unit": "pcs", "price": 150.0, "min_stock": 50},
                    {"name": "Bed Sheet (King)", "unit": "pcs", "price": 800.0, "min_stock": 40},
                    {"name": "Pillow Cover", "unit": "pcs", "price": 100.0, "min_stock": 80},
                    {"name": "Bath Robe", "unit": "pcs", "price": 1200.0, "min_stock": 20}
                ]
            },
            {
                "name": "Housekeeping - Toiletries",
                "department": "Housekeeping",
                "items": [
                    {"name": "Soap Bar (Small)", "unit": "pcs", "price": 10.0, "min_stock": 200},
                    {"name": "Shampoo Bottle (30ml)", "unit": "bottle", "price": 15.0, "min_stock": 200},
                    {"name": "Toothpaste Kit", "unit": "kit", "price": 12.0, "min_stock": 100},
                    {"name": "Toilet Paper Roll", "unit": "roll", "price": 25.0, "min_stock": 100},
                    {"name": "Floor Cleaner Liquid", "unit": "liter", "price": 150.0, "min_stock": 10}
                ]
            },
            {
                "name": "Maintenance - Electrical",
                "department": "Maintenance",
                "is_asset_fixed": True,
                "items": [
                    {"name": "LED Bulb 9W", "unit": "pcs", "price": 80.0, "min_stock": 20},
                    {"name": "Tube Light 20W", "unit": "pcs", "price": 250.0, "min_stock": 15},
                    {"name": "Extension Cord", "unit": "pcs", "price": 300.0, "min_stock": 5},
                    {"name": "3-Pin Plug", "unit": "pcs", "price": 40.0, "min_stock": 30},
                    {"name": "Electrical Tape", "unit": "roll", "price": 20.0, "min_stock": 10}
                ]
            },
             {
                "name": "Office Supplies",
                "department": "Front Office",
                "items": [
                    {"name": "A4 Paper Ream", "unit": "ream", "price": 220.0, "min_stock": 10},
                    {"name": "Ballpoint Pen (Blue)", "unit": "box", "price": 100.0, "min_stock": 5},
                    {"name": "Stapler", "unit": "pcs", "price": 150.0, "min_stock": 2},
                    {"name": "Notepads", "unit": "pcs", "price": 30.0, "min_stock": 50},
                    {"name": "Printer Toner", "unit": "cartridge", "price": 1500.0, "min_stock": 2}
                ]
            }
        ]

        # 4. Create Data
        for cat_data in categories_data:
            # Create/Get Category
            category = db.query(InventoryCategory).filter(InventoryCategory.name == cat_data["name"]).first()
            if not category:
                category = InventoryCategory(
                    name=cat_data["name"],
                    parent_department=cat_data["department"],
                    track_laundry=cat_data.get("track_laundry", False),
                    is_asset_fixed=cat_data.get("is_asset_fixed", False),
                    is_active=True
                )
                db.add(category)
                db.commit()
                db.refresh(category)
                print(f"  + Category Created: {category.name}")
            else:
                print(f"  . Category Exists: {category.name}")

            # Create Items for this Category
            for item_data in cat_data["items"]:
                item = db.query(InventoryItem).filter(InventoryItem.name == item_data["name"]).first()
                if not item:
                    # Generate a random item code
                    item_code = f"ITM-{random.randint(1000, 9999)}"
                    
                    item = InventoryItem(
                        name=item_data["name"],
                        category_id=category.id,
                        unit=item_data["unit"],
                        unit_price=item_data["price"],
                        selling_price=item_data.get("selling_price"),
                        min_stock_level=item_data["min_stock"],
                        current_stock=100.0, # Initial seed stock
                        item_code=item_code,
                        is_perishable=item_data.get("is_perishable", False),
                        is_sellable_to_guest=item_data.get("is_sellable", False),
                        preferred_vendor_id=vendor.id,
                        location="Main Warehouse"
                    )
                    db.add(item)
                    db.commit()
                    db.refresh(item)
                    
                    # Add stock to warehouse
                    stock_entry = LocationStock(
                        location_id=warehouse.id,
                        item_id=item.id,
                        quantity=100.0,
                        last_updated=datetime.now(timezone.utc)
                    )
                    db.add(stock_entry)
                    db.commit()
                    print(f"    - Item Created: {item.name}")
                else:
                     print(f"    . Item Exists: {item.name}")

        print("\nInventory Seeding Completed Successfully!")

    except Exception as e:
        print(f"Error Seeding Inventory: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_inventory()
