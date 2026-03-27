"""
Restore Coca Cola and Mineral Water stock to purchased amounts
"""
from app.database import SessionLocal
from app.models.inventory import InventoryItem, InventoryTransaction
from datetime import datetime


def restore_beverage_stock():
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("RESTORE COCA COLA & MINERAL WATER STOCK")
        print("=" * 70)
        print()
        
        # Find Coca Cola
        coca_cola = db.query(InventoryItem).filter(
            InventoryItem.name.ilike("%Coca Cola%")
        ).first()
        
        # Find Mineral Water
        water = db.query(InventoryItem).filter(
            InventoryItem.name.ilike("%Mineral Water%")
        ).first()
        
        if not coca_cola:
            print("❌ Coca Cola not found")
            return
        
        if not water:
            print("❌ Mineral Water not found")
            return
        
        print("Current Status:")
        print(f"  Coca Cola: {coca_cola.current_stock} {coca_cola.unit}")
        print(f"  Mineral Water: {water.current_stock} {water.unit}")
        print()
        
        # Restore to purchased amounts (based on earlier purchases)
        coca_cola_qty = 50.0  # Original purchase was 50 pcs
        water_qty = 40.0      # Original purchase was 40 pcs
        
        print("Proposed Restoration:")
        print(f"  Coca Cola: {coca_cola.current_stock} → {coca_cola_qty} {coca_cola.unit}")
        print(f"  Mineral Water: {water.current_stock} → {water_qty} {water.unit}")
        print()
        
        confirm = input("Restore stock to these values? (yes/no): ").strip().lower()
        
        if confirm != "yes":
            print("❌ Operation cancelled")
            return
        
        print()
        print("=" * 70)
        print("RESTORING STOCK...")
        print("=" * 70)
        print()
        
        # Update Coca Cola
        coca_cola.current_stock = coca_cola_qty
        
        # Create purchase transaction for Coca Cola
        coca_txn = InventoryTransaction(
            item_id=coca_cola.id,
            transaction_type="purchase",
            quantity=coca_cola_qty,
            unit_price=coca_cola.unit_price,
            total_amount=coca_cola.unit_price * coca_cola_qty if coca_cola.unit_price else None,
            reference_number="PO-RESTORE-001",
            department=coca_cola.category.parent_department if coca_cola.category else "Facility",
            notes="Stock restoration after transaction cleanup",
            created_by=None,
            created_at=datetime.utcnow()
        )
        db.add(coca_txn)
        
        print(f"✅ Coca Cola: Restored to {coca_cola_qty} {coca_cola.unit}")
        
        # Update Mineral Water
        water.current_stock = water_qty
        
        # Create purchase transaction for Water
        water_txn = InventoryTransaction(
            item_id=water.id,
            transaction_type="purchase",
            quantity=water_qty,
            unit_price=water.unit_price,
            total_amount=water.unit_price * water_qty if water.unit_price else None,
            reference_number="PO-RESTORE-002",
            department=water.category.parent_department if water.category else "Facility",
            notes="Stock restoration after transaction cleanup",
            created_by=None,
            created_at=datetime.utcnow()
        )
        db.add(water_txn)
        
        print(f"✅ Mineral Water: Restored to {water_qty} {water.unit}")
        
        db.commit()
        
        print()
        print("=" * 70)
        print("✅ STOCK RESTORED SUCCESSFULLY!")
        print("=" * 70)
        print()
        print("Updated Stock:")
        print(f"  Coca Cola 750ml: {coca_cola_qty} pcs")
        print(f"  Mineral Water 1L: {water_qty} pcs")
        print()
        print("Purchase transactions created:")
        print(f"  - PO-RESTORE-001 (Coca Cola)")
        print(f"  - PO-RESTORE-002 (Mineral Water)")
        print()
        print("Refresh your inventory page to see the updated stock.")
        print()
        
    except Exception as e:
        db.rollback()
        print()
        print("=" * 70)
        print("❌ ERROR")
        print("=" * 70)
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


if __name__ == "__main__":
    restore_beverage_stock()
