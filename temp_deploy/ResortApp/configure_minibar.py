from app.database import SessionLocal
from app.models.inventory import InventoryItem, LocationStock, InventoryCategory

db = SessionLocal()

def configure_minibar_policy():
    print("Configuring Minibar Policy for Room 104...")
    
    # 1. Update Water to be Complimentary (Limit 2)
    water = db.query(InventoryItem).filter(InventoryItem.name == "Premium Mineral Water 1 Liter").first()
    if water:
        water.complimentary_limit = 2
        water.selling_price = 40.0 # Price if they exceed limit
        print(f"Updated '{water.name}': Set Complimentary Limit = 2, Selling Price = 40.0")
    
    # 2. Create/Update Coca Cola (Payable)
    coke = db.query(InventoryItem).filter(InventoryItem.name == "Coca Cola 300ml").first()
    if not coke:
        # Find a category (Non-Alcoholic Beverages)
        category = db.query(InventoryCategory).filter(InventoryCategory.name == "Non-Alcoholic Beverages").first()
        if not category:
            # Fallback
            category = db.query(InventoryCategory).first()

        coke = InventoryItem(
            name="Coca Cola 300ml",
            category_id=category.id,
            unit="pcs",
            current_stock=100,
            unit_price=30.0, # Cost
            selling_price=60.0, # Price to guest
            complimentary_limit=0, # Not free
            is_sellable_to_guest=True
        )
        db.add(coke)
        db.commit() # Commit to get ID
        db.refresh(coke)
        print(f"Created new item: '{coke.name}'")
    else:
        coke.selling_price = 60.0
        coke.complimentary_limit = 0
        print(f"Updated '{coke.name}': Set Price = 60.0, Free Limit = 0")

    # 3. Stock Room 104 with Coke
    # Room 104 location_id is 10 (from previous debug)
    loc_stock = db.query(LocationStock).filter(
        LocationStock.location_id == 10,
        LocationStock.item_id == coke.id
    ).first()
    
    if not loc_stock:
        loc_stock = LocationStock(
            location_id=10,
            item_id=coke.id,
            quantity=2.0
        )
        db.add(loc_stock)
        print(f"Added 2x '{coke.name}' to Room 104")
    else:
        loc_stock.quantity = 2.0
        print(f"Ensured 2x '{coke.name}' in Room 104")

    db.commit()
    print("Configuration complete.")

if __name__ == "__main__":
    configure_minibar_policy()
