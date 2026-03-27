"""
Script to clear stock for specific items or all items
"""
import sys
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.inventory import InventoryItem, InventoryTransaction, LocationStock


def clear_item_stock(item_name=None, clear_all=False):
    """Clear stock for a specific item or all items"""
    db: Session = SessionLocal()
    
    try:
        print("=" * 60)
        print("INVENTORY STOCK CLEANER")
        print("=" * 60)
        print()
        
        if clear_all:
            # Get all items
            items = db.query(InventoryItem).all()
            print(f"📦 Found {len(items)} items in inventory")
        elif item_name:
            # Find specific item
            items = db.query(InventoryItem).filter(
                InventoryItem.name.ilike(f"%{item_name}%")
            ).all()
            print(f"🔍 Searching for items matching '{item_name}'...")
            print(f"📦 Found {len(items)} matching items")
        else:
            print("❌ Error: Please specify either item_name or clear_all=True")
            return
        
        if not items:
            print("❌ No items found!")
            return
        
        print()
        print("Items to clear:")
        for item in items:
            print(f"  - {item.name} (Current Stock: {item.current_stock} {item.unit})")
        print()
        
        response = input("Are you sure you want to clear stock for these items? (yes/no): ").strip().lower()
        
        if response != "yes":
            print("❌ Operation cancelled.")
            return
        
        print()
        print("🗑️  Clearing stock...")
        print()
        
        total_transactions_deleted = 0
        total_location_stock_deleted = 0
        
        for item in items:
            # Delete all transactions for this item
            deleted_txn = db.query(InventoryTransaction).filter(
                InventoryTransaction.item_id == item.id
            ).delete()
            total_transactions_deleted += deleted_txn
            
            # Delete all location stock for this item
            deleted_loc = db.query(LocationStock).filter(
                LocationStock.item_id == item.id
            ).delete()
            total_location_stock_deleted += deleted_loc
            
            # Reset item stock to 0
            old_stock = item.current_stock
            item.current_stock = 0
            
            print(f"  ✓ {item.name}: {old_stock} → 0 {item.unit}")
            print(f"    - Deleted {deleted_txn} transactions")
            print(f"    - Deleted {deleted_loc} location stock records")
        
        db.commit()
        
        print()
        print("=" * 60)
        print("✅ SUCCESS! Stock cleared.")
        print("=" * 60)
        print()
        print("📊 Summary:")
        print(f"   - Items updated: {len(items)}")
        print(f"   - Transactions deleted: {total_transactions_deleted}")
        print(f"   - Location stock records deleted: {total_location_stock_deleted}")
        print()
        
    except Exception as e:
        db.rollback()
        print()
        print("=" * 60)
        print("❌ ERROR occurred!")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print()
        print("Database has been rolled back. No changes were made.")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        
    finally:
        db.close()


if __name__ == "__main__":
    # Example usage:
    # To clear a specific item:
    clear_item_stock(item_name="Kitchen Hand Towel")
    
    # To clear all items:
    # clear_item_stock(clear_all=True)
