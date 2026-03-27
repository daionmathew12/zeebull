"""
Fix water over-deduction - add back 4 pcs that were deducted twice
"""
from app.database import SessionLocal
from app.models.inventory import InventoryItem, InventoryTransaction
from datetime import datetime


def fix_water_overdeduction():
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("FIX WATER OVER-DEDUCTION")
        print("=" * 70)
        print()
        
        # Find Mineral Water
        water = db.query(InventoryItem).filter(
            InventoryItem.name.ilike("%Mineral Water%")
        ).first()
        
        if not water:
            print("❌ Mineral Water not found")
            return
        
        print(f"📦 Item: {water.name}")
        print(f"   Current Stock: {water.current_stock} {water.unit}")
        print()
        
        # Calculate from transaction history
        transactions = db.query(InventoryTransaction).filter(
            InventoryTransaction.item_id == water.id
        ).order_by(InventoryTransaction.created_at).all()
        
        print("Transaction History:")
        print()
        
        calculated_stock = 0.0
        for txn in transactions:
            if txn.transaction_type in ["in", "purchase", "adjustment", "transfer_in"]:
                calculated_stock += txn.quantity
                print(f"  ✅ {txn.transaction_type.upper():15} +{txn.quantity:6.1f} {water.unit:5} → {calculated_stock:6.1f} | {txn.reference_number or 'N/A'}")
            elif txn.transaction_type in ["out", "consumption", "transfer_out"]:
                calculated_stock -= txn.quantity
                print(f"  ❌ {txn.transaction_type.upper():15} -{txn.quantity:6.1f} {water.unit:5} → {calculated_stock:6.1f} | {txn.reference_number or 'N/A'}")
        
        print()
        print("=" * 70)
        print("ANALYSIS")
        print("=" * 70)
        print(f"  Current Stock (Database):     {water.current_stock:6.1f} {water.unit}")
        print(f"  Calculated Stock (History):   {calculated_stock:6.1f} {water.unit}")
        print(f"  Discrepancy:                  {water.current_stock - calculated_stock:6.1f} {water.unit}")
        print()
        
        if water.current_stock < calculated_stock:
            over_deducted = calculated_stock - water.current_stock
            print(f"⚠️  Water was OVER-DEDUCTED by {over_deducted} {water.unit}")
            print()
            print(f"Proposed fix: Add back {over_deducted} {water.unit} to stock")
            print(f"              {water.current_stock} → {calculated_stock} {water.unit}")
            print()
            
            confirm = input("Apply this fix? (yes/no): ").strip().lower()
            
            if confirm != "yes":
                print("❌ Fix cancelled")
                return
            
            # Add back the over-deducted amount
            old_stock = water.current_stock
            water.current_stock = calculated_stock
            
            # Create adjustment transaction
            transaction = InventoryTransaction(
                item_id=water.id,
                transaction_type="adjustment",
                quantity=over_deducted,
                unit_price=water.unit_price,
                total_amount=0,  # Adjustment, no cost
                reference_number="ADJ-OVERDEDUCTION-FIX",
                department=water.category.parent_department if water.category else "Housekeeping",
                notes=f"Adjustment to fix over-deduction - Water was deducted twice for Room 102",
                created_by=None,
                created_at=datetime.utcnow()
            )
            db.add(transaction)
            db.commit()
            
            print()
            print("=" * 70)
            print("✅ FIXED!")
            print("=" * 70)
            print(f"  Added back: {over_deducted} {water.unit}")
            print(f"  Stock updated: {old_stock} → {water.current_stock} {water.unit}")
            print(f"  Adjustment transaction created: ADJ-OVERDEDUCTION-FIX")
            print()
        else:
            print("✅ Stock matches history, no fix needed")
        
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
    fix_water_overdeduction()
