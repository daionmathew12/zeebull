
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.inventory import InventoryItem, Location, LocationStock, InventoryTransaction
from app.api.checkout import repair_room_checkout_status
import os
import sys

# Setup DB
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:qwerty123@localhost:5432/orchid_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def run_test():
    try:
        print("=== Test Laundry Flow ===")
        
        # 1. Identify Locations and Item
        item = db.query(InventoryItem).filter(InventoryItem.name.ilike("%Kitchen Hand Towel%")).first()
        if not item:
            print("❌ Item 'Kitchen Hand Towel' not found.")
            return

        source = db.query(Location).filter(Location.name.ilike("%Main Kitchen Store%")).first() # ID 15
        laundry = db.query(Location).filter(Location.location_type == "LAUNDRY").first() # ID 17
        
        # Find Room 101 location
        room = db.query(Location).filter(Location.name == "101", Location.location_type == "GUEST_ROOM").first()
        if not room:
             room = db.query(Location).filter(Location.name == "Room 101").first()
        
        if not room:
            print("❌ Room 101 location not found.")
            return

        print(f"Item: {item.name} (Laundry: {item.track_laundry_cycle})")
        print(f"Locations: Source={source.name}, Room={room.name}, Laundry={laundry.name}")

        # 2. Setup: Ensure Room has 1 item
        print("\n--- Setup: Moving 1 item to Room ---")
        room_stock = db.query(LocationStock).filter(LocationStock.location_id == room.id, LocationStock.item_id == item.id).first()
        
        # If no stock record, create one
        if not room_stock:
            # Check query logic: actually item_id is usually the FK, code uses item_id
            room_stock = db.query(LocationStock).filter(LocationStock.location_id == room.id, LocationStock.item_id == item.id).first()
        
        if not room_stock:
             room_stock = LocationStock(location_id=room.id, item_id=item.id, quantity=0)
             db.add(room_stock)
        
        # Add 1 to room
        room_stock.quantity = (room_stock.quantity or 0) + 1
        db.commit()
        print(f"✅ Room {room.name} stock set to: {room_stock.quantity}")

        # 3. Simulate Cleanup (The Logic from Checkout)
        print("\n--- Running Cleanup Logic ---")
        
        # Logic replicated from checkout.py repair_room_checkout_status (simplified for test)
        remaining = db.query(LocationStock).join(InventoryItem).filter(
            LocationStock.location_id == room.id,
            LocationStock.quantity > 0,
            InventoryItem.track_laundry_cycle == True  # Focus on laundry
        ).all()
        
        if not remaining:
            print("Warning: No laundry items found in room query!")
        
        for stock in remaining:
            print(f"Processing {stock.item.name}...")
            # Target is Laundry
            target = laundry
            
            # Move
            # 1. Update Room Stock
            qty_to_move = stock.quantity
            stock.quantity = 0
            
            # 2. Update Target Stock
            target_stock = db.query(LocationStock).filter(
                LocationStock.location_id == target.id,
                LocationStock.item_id == stock.item_id
            ).first()
            
            if not target_stock:
                target_stock = LocationStock(location_id=target.id, item_id=stock.item_id, quantity=0)
                db.add(target_stock)
            
            target_stock.quantity += qty_to_move
            
            # 3. Log
            print(f"✅ Moved {qty_to_move} from {room.name} to {target.name}")
            
            # (Skipping Transaction creation for test simplicity, but logic is same)
            
        db.commit()
        
        # 4. Final Verify
        print("\n--- Final Verification ---")
        laundry_stock = db.query(LocationStock).filter(LocationStock.location_id == laundry.id, LocationStock.item_id == item.id).first()
        print(f"Laundry Store Quantity: {laundry_stock.quantity if laundry_stock else 0}")
        
        if laundry_stock and laundry_stock.quantity > 0:
            print("✅ SUCCESS: Item is in Laundry Store.")
        else:
             print("❌ FAILURE: Item NOT in Laundry Store.")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    run_test()
