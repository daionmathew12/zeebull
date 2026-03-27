"""
Reset all inventory stock to match purchases + initial stock (as if nothing has been used)
This will recalculate stock based on purchase and adjustment transactions only
"""
from app.database import SessionLocal
from app.models.inventory import InventoryItem, InventoryTransaction
from sqlalchemy import func


def reset_stock_to_unused():
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("RESET INVENTORY STOCK TO UNUSED STATE")
        print("=" * 70)
        print()
        print("This will reset all inventory stock levels to match:")
        print("  - Purchases (IN transactions)")
        print("  - Initial stock (ADJUSTMENT transactions)")
        print("  - Transfer IN transactions")
        print()
        print("As if nothing has been consumed or used yet.")
        print()
        print("⚠️  WARNING: This will overwrite current stock levels!")
        print()
        
        # Get all inventory items
        items = db.query(InventoryItem).all()
        
        print(f"Found {len(items)} inventory items")
        print()
        
        # Calculate totals for each item
        item_updates = []
        
        for item in items:
            # Get all IN transactions for this item
            in_total = db.query(func.sum(InventoryTransaction.quantity)).filter(
                InventoryTransaction.item_id == item.id,
                InventoryTransaction.transaction_type.in_(["in", "purchase", "adjustment", "transfer_in"])
            ).scalar() or 0.0
            
            current_stock = item.current_stock
            
            if abs(current_stock - in_total) > 0.01:  # Allow small floating point differences
                item_updates.append({
                    'item': item,
                    'current_stock': current_stock,
                    'calculated_stock': in_total,
                    'difference': in_total - current_stock
                })
        
        if not item_updates:
            print("✅ All items already match calculated totals. No updates needed.")
            return
        
        print(f"Items to update: {len(item_updates)}")
        print()
        print("=" * 70)
        print("PREVIEW OF CHANGES")
        print("=" * 70)
        print()
        
        for update in item_updates:
            item = update['item']
            print(f"📦 {item.name}")
            print(f"   Current Stock: {update['current_stock']:.1f} {item.unit}")
            print(f"   Calculated Stock (Unused): {update['calculated_stock']:.1f} {item.unit}")
            print(f"   Change: {update['difference']:+.1f} {item.unit}")
            print()
        
        confirm = input("Apply these changes? (yes/no): ").strip().lower()
        
        if confirm != "yes":
            print("❌ Operation cancelled")
            return
        
        print()
        print("=" * 70)
        print("UPDATING STOCK LEVELS...")
        print("=" * 70)
        print()
        
        for update in item_updates:
            item = update['item']
            old_stock = item.current_stock
            new_stock = update['calculated_stock']
            
            item.current_stock = new_stock
            
            print(f"✅ {item.name}: {old_stock:.1f} → {new_stock:.1f} {item.unit}")
        
        db.commit()
        
        print()
        print("=" * 70)
        print("✅ STOCK LEVELS RESET SUCCESSFULLY!")
        print("=" * 70)
        print()
        print(f"Updated {len(item_updates)} items")
        print()
        print("All inventory stock now reflects unused state:")
        print("  - Purchases + Initial Stock + Transfers IN")
        print("  - No consumption or usage deducted")
        print()
        print("Refresh your inventory page to see the updated stock levels.")
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
    reset_stock_to_unused()
