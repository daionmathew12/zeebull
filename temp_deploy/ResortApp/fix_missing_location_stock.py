
import sys
import os
from sqlalchemy import func

# Add root directory to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.inventory import InventoryItem, InventoryTransaction, LocationStock, PurchaseMaster, PurchaseDetail

def fix_stock():
    db = SessionLocal()
    try:
        print("--- Fixing Location Stock Discrepancies ---")
        
        # We focus on Mineral Water (20) and Coca Cola (19) as requested, but logic is general
        # However, to be safe, let's just target these two first or items with discrepancies.
        
        items = db.query(InventoryItem).filter(InventoryItem.id.in_([19, 20])).all()
        
        for item in items:
            print(f"\nProcessing Item: {item.name} (ID: {item.id})")
            
            # 1. Calculate Expected Stock from Transactions
            txns = db.query(InventoryTransaction).filter(InventoryTransaction.item_id == item.id).all()
            calc_stock = 0
            for txn in txns:
                qty = txn.quantity
                sign = 0
                if txn.transaction_type in ['in', 'purchase', 'checkin', 'stock received', 'transfer_in']:
                    sign = 1
                elif txn.transaction_type in ['out', 'issue', 'waste', 'checkout', 'transfer_out']:
                    sign = -1
                calc_stock += (qty * sign)
            
            print(f"  Calculated Stock from Transactions: {calc_stock}")
            print(f"  Current DB Stock: {item.current_stock}")
            
            # 2. Check Location Stock Sum
            loc_stocks = db.query(LocationStock).filter(LocationStock.item_id == item.id).all()
            loc_sum = sum([ls.quantity for ls in loc_stocks])
            print(f"  Location Stock Sum: {loc_sum}")
            
            missing_stock = calc_stock - loc_sum
            
            if missing_stock > 0:
                print(f"  [MISSING] {missing_stock} units are unaccounted for in LocationStock.")
                
                # Find where they should be. Default to Purchase Destination (Location 15)
                # We prioritize the latest purchase dest location
                target_loc_id = 15 # Default from investigation
                
                # Check recent purchase
                last_purchase_detail = db.query(PurchaseDetail).filter(PurchaseDetail.item_id == item.id).order_by(PurchaseDetail.id.desc()).first()
                if last_purchase_detail:
                    pm = db.query(PurchaseMaster).filter(PurchaseMaster.id == last_purchase_detail.purchase_master_id).first()
                    if pm and pm.destination_location_id:
                        target_loc_id = pm.destination_location_id
                        print(f"  > Found target location from Purchase #{pm.id}: {target_loc_id}")
                
                print(f"  > Allocating {missing_stock} units to Location {target_loc_id}...")
                
                # Update or Create LocationStock
                ls_entry = db.query(LocationStock).filter(
                    LocationStock.item_id == item.id,
                    LocationStock.location_id == target_loc_id
                ).first()
                
                if ls_entry:
                    ls_entry.quantity += missing_stock
                    print(f"  > Updated existing LocationStock for Loc {target_loc_id}")
                else:
                    new_ls = LocationStock(
                        item_id=item.id,
                        location_id=target_loc_id,
                        quantity=missing_stock
                    )
                    db.add(new_ls)
                    print(f"  > Created new LocationStock for Loc {target_loc_id}")
                
                # 3. Update Global Stock if needed
                if item.current_stock != calc_stock:
                    print(f"  > Updating InventoryItem.current_stock from {item.current_stock} to {calc_stock}")
                    item.current_stock = calc_stock
                
                db.commit()
                print("  [SUCCESS] Stock Reconciled.")
                
            elif missing_stock < 0:
                print(f"  [WARNING] LocationStock sum ({loc_sum}) exceeds calculated stock ({calc_stock}). Check manual edits.")
            else:
                print("  [OK] Location stock matches calculated stock.")

    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_stock()
