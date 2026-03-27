import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Add parent directory to path
sys.path.append(os.getcwd())

from app.database import SQLALCHEMY_DATABASE_URL
from app.models.inventory import Location, LocationStock, InventoryItem, InventoryTransaction
from app.models.user import User

def add_stock():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        print("--- ADDING TEST STOCK ---")
        
        # 1. Find Admin User
        admin = db.query(User).filter(User.email == "admin@example.com").first()
        if not admin:
            # try first user
            admin = db.query(User).first()
        
        user_id = admin.id if admin else 1
        
        # 2. Find Warehouse
        warehouse = db.query(Location).filter(Location.location_type.in_(['WAREHOUSE', 'CENTRAL_WAREHOUSE'])).first()
        if not warehouse:
             warehouse = db.query(Location).first() # Fallback
        
        print(f"Using Location: {warehouse.name}")

        # 3. Add Stock for specific items
        # User screenshot showed errors for "Mineral Water 1L" and "Coca Cola 750ml"
        items_to_fix = ["Mineral Water 1L", "Coca Cola 750ml"]
        
        for item_name in items_to_fix:
            item = db.query(InventoryItem).filter(InventoryItem.name.ilike(f"%{item_name}%")).first()
            if item:
                qty_to_add = 100
                
                # Update Location Stock
                stock = db.query(LocationStock).filter(LocationStock.location_id == warehouse.id, LocationStock.item_id == item.id).first()
                if stock:
                    old_qty = stock.quantity
                    stock.quantity += qty_to_add
                    stock.last_updated = datetime.utcnow()
                    print(f"Updated {item.name}: {old_qty} -> {stock.quantity}")
                else:
                    new_stock = LocationStock(
                        location_id=warehouse.id,
                        item_id=item.id,
                        quantity=qty_to_add,
                        last_updated=datetime.utcnow()
                    )
                    db.add(new_stock)
                    print(f"Created stock for {item.name}: {qty_to_add}")
                
                # Update Global Stock
                if item.current_stock is None: item.current_stock = 0
                item.current_stock += qty_to_add
                
                # Log Transaction
                txn = InventoryTransaction(
                    item_id=item.id,
                    transaction_type="in", # Purchase/In
                    quantity=qty_to_add,
                    unit_price=item.unit_price or 10,
                    total_amount=qty_to_add * (item.unit_price or 10),
                    reference_number="TEST-STOCK-ADD",
                    notes=f"Test stock added to unblock allocation testing",
                    created_by=user_id,
                    created_at=datetime.utcnow()
                )
                db.add(txn)
            else:
                print(f"Warning: Item containing '{item_name}' not found.")
        
        db.commit()
        print("Successfully added test stock.")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_stock()
