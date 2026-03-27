"""
Manually deduct Coca Cola that should have been deducted at check-in
"""
from app.database import SessionLocal
from app.models.inventory import InventoryItem, InventoryTransaction, LocationStock
from app.models.room import Room
from datetime import datetime


def manual_deduct_coca_cola():
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("MANUAL INVENTORY DEDUCTION - COCA COLA")
        print("=" * 60)
        print()
        
        # Find Coca Cola
        coca_cola = db.query(InventoryItem).filter(
            InventoryItem.name.ilike("%Coca Cola%")
        ).first()
        
        if not coca_cola:
            print("❌ Coca Cola not found in inventory")
            return
        
        print(f"📦 Found: {coca_cola.name}")
        print(f"   Current Stock: {coca_cola.current_stock} {coca_cola.unit}")
        print(f"   Unit Price: ₹{coca_cola.unit_price or 0}")
        print()
        
        # Ask for room number
        room_number = input("Enter room number (e.g., 102): ").strip()
        
        # Find room
        room = db.query(Room).filter(Room.number == room_number).first()
        if not room:
            print(f"❌ Room {room_number} not found")
            return
        
        print(f"🏠 Room: {room.number}")
        print()
        
        # Ask for quantity
        quantity_input = input(f"Enter quantity to deduct (default: 1): ").strip()
        quantity = float(quantity_input) if quantity_input else 1.0
        
        print()
        print("=" * 60)
        print("CONFIRMATION")
        print("=" * 60)
        print(f"  Item: {coca_cola.name}")
        print(f"  Current Stock: {coca_cola.current_stock} {coca_cola.unit}")
        print(f"  Quantity to Deduct: {quantity} {coca_cola.unit}")
        print(f"  New Stock: {coca_cola.current_stock - quantity} {coca_cola.unit}")
        print(f"  Room: {room.number}")
        print()
        
        confirm = input("Proceed with deduction? (yes/no): ").strip().lower()
        
        if confirm != "yes":
            print("❌ Operation cancelled")
            return
        
        # Deduct from global stock
        old_stock = coca_cola.current_stock
        coca_cola.current_stock -= quantity
        
        # Create transaction
        transaction = InventoryTransaction(
            item_id=coca_cola.id,
            transaction_type="out",
            quantity=quantity,
            unit_price=coca_cola.unit_price,
            total_amount=coca_cola.unit_price * quantity if coca_cola.unit_price else None,
            reference_number=f"MANUAL-CHECKIN-{room.number}",
            department=coca_cola.category.parent_department if coca_cola.category else "Housekeeping",
            notes=f"Manual deduction for check-in - Room {room.number} (missed during automatic assignment)",
            created_by=None,
            created_at=datetime.utcnow()
        )
        db.add(transaction)
        
        # Update location stock if exists
        location_stocks = db.query(LocationStock).filter(
            LocationStock.item_id == coca_cola.id
        ).all()
        
        if location_stocks:
            # Deduct from first available location
            location_stock = location_stocks[0]
            old_loc_stock = location_stock.quantity
            location_stock.quantity -= quantity
            print(f"   Updated location stock: {location_stock.location.name if location_stock.location else 'Unknown'}")
            print(f"   {old_loc_stock} → {location_stock.quantity} {coca_cola.unit}")
        
        db.commit()
        
        print()
        print("=" * 60)
        print("✅ SUCCESS!")
        print("=" * 60)
        print(f"  Deducted {quantity} {coca_cola.unit} of {coca_cola.name}")
        print(f"  Global Stock: {old_stock} → {coca_cola.current_stock} {coca_cola.unit}")
        print(f"  Transaction created: {transaction.reference_number}")
        print(f"  Room: {room.number}")
        print()
        
    except Exception as e:
        db.rollback()
        print()
        print("=" * 60)
        print("❌ ERROR")
        print("=" * 60)
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


if __name__ == "__main__":
    manual_deduct_coca_cola()
