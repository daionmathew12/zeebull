"""
Fix stock discrepancy by syncing current_stock with transaction history
"""
from app.database import SessionLocal
from app.models.inventory import InventoryItem, InventoryTransaction
from sqlalchemy import func


def fix_stock_discrepancy():
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("FIX STOCK DISCREPANCY - SYNC WITH TRANSACTION HISTORY")
        print("=" * 70)
        print()
        
        # Find Coca Cola
        coca_cola = db.query(InventoryItem).filter(
            InventoryItem.name.ilike("%Coca Cola%")
        ).first()
        
        if not coca_cola:
            print("❌ Coca Cola not found")
            return
        
        print(f"📦 Item: {coca_cola.name}")
        print(f"   Current Stock (Database): {coca_cola.current_stock} {coca_cola.unit}")
        print()
        
        # Calculate stock from transaction history
        print("📊 Calculating stock from transaction history...")
        print()
        
        # Get all transactions for this item
        transactions = db.query(InventoryTransaction).filter(
            InventoryTransaction.item_id == coca_cola.id
        ).order_by(InventoryTransaction.created_at).all()
        
        print(f"Found {len(transactions)} transactions:")
        print()
        
        calculated_stock = 0.0
        
        for txn in transactions:
            if txn.transaction_type in ["in", "purchase", "adjustment", "transfer_in"]:
                calculated_stock += txn.quantity
                print(f"  ✅ {txn.transaction_type.upper():15} +{txn.quantity:6.1f} {coca_cola.unit:5} → {calculated_stock:6.1f} | {txn.reference_number or 'N/A'}")
            elif txn.transaction_type in ["out", "consumption", "transfer_out"]:
                calculated_stock -= txn.quantity
                print(f"  ❌ {txn.transaction_type.upper():15} -{txn.quantity:6.1f} {coca_cola.unit:5} → {calculated_stock:6.1f} | {txn.reference_number or 'N/A'}")
            else:
                print(f"  ⚠️  {txn.transaction_type.upper():15}  {txn.quantity:6.1f} {coca_cola.unit:5} → {calculated_stock:6.1f} | {txn.reference_number or 'N/A'}")
        
        print()
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"  Current Stock (Database):     {coca_cola.current_stock:6.1f} {coca_cola.unit}")
        print(f"  Calculated Stock (History):   {calculated_stock:6.1f} {coca_cola.unit}")
        print(f"  Discrepancy:                  {coca_cola.current_stock - calculated_stock:6.1f} {coca_cola.unit}")
        print()
        
        if abs(coca_cola.current_stock - calculated_stock) < 0.01:
            print("✅ Stock is already in sync! No fix needed.")
            return
        
        print("⚠️  Stock discrepancy detected!")
        print()
        print(f"Proposed fix: Update current_stock from {coca_cola.current_stock} to {calculated_stock}")
        print()
        
        confirm = input("Apply this fix? (yes/no): ").strip().lower()
        
        if confirm != "yes":
            print("❌ Fix cancelled")
            return
        
        # Update stock
        old_stock = coca_cola.current_stock
        coca_cola.current_stock = calculated_stock
        db.commit()
        
        print()
        print("=" * 70)
        print("✅ FIXED!")
        print("=" * 70)
        print(f"  Updated stock: {old_stock} → {calculated_stock} {coca_cola.unit}")
        print(f"  Discrepancy resolved: {old_stock - calculated_stock:+.1f} {coca_cola.unit}")
        print()
        print("Refresh your inventory page to see the corrected stock.")
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
    fix_stock_discrepancy()
