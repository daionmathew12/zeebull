"""
Corrective script: manually execute the return transactions that were missed
for CheckoutRequest ID=29, Room 101 (TV returned to 'qwerty' location, ID=3).
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ResortApp')))

from app.database import SessionLocal
from app.models.checkout import CheckoutRequest
from app.models.inventory import (
    InventoryTransaction, LocationStock, Location,
    StockIssueDetail, StockIssue, InventoryItem
)
from app.models.room import Room
from datetime import datetime

def fix_missed_return():
    db = SessionLocal()
    try:
        req = db.query(CheckoutRequest).filter(CheckoutRequest.id == 29).first()
        if not req:
            print("CheckoutRequest 29 not found.")
            return

        print(f"Processing missed returns for CheckoutRequest {req.id}, Room {req.room_number}")

        room = db.query(Room).filter(Room.number == req.room_number).first()
        if not room or not room.inventory_location_id:
            print("Room or location not found.")
            return
        
        room_loc_id = room.inventory_location_id

        # Process each rentable item from inventory_data
        for entry in (req.inventory_data or []):
            if not entry.get('is_rentable'):
                continue
            
            item_id = entry.get('item_id')
            return_location_id = entry.get('return_location_id')
            
            if not item_id or not return_location_id:
                print(f"  Skipping item {item_id}: no return_location_id")
                continue
            
            inv_item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
            if not inv_item:
                continue

            # Find how much was actually issued to the room
            issued_qty = db.query(
                __import__('sqlalchemy', fromlist=['func']).func.sum(StockIssueDetail.issued_quantity)
            ).join(StockIssue).filter(
                StockIssue.destination_location_id == room_loc_id,
                StockIssueDetail.item_id == item_id
            ).scalar() or 0.0
            issued_qty = float(issued_qty)

            total_lost = float(entry.get('used_qty', 0)) + float(entry.get('missing_qty', 0)) + float(entry.get('damage_qty', 0))
            return_qty = max(0, issued_qty - total_lost)

            print(f"  Item: {inv_item.name}, Issued: {issued_qty}, Lost: {total_lost}, Return: {return_qty} -> Loc {return_location_id}")

            if return_qty <= 0:
                print(f"  Nothing to return for {inv_item.name}")
                continue

            # Check if transaction already exists
            existing = db.query(InventoryTransaction).filter(
                InventoryTransaction.reference_number == f"CHKINV-RET-{req.id}",
                InventoryTransaction.item_id == item_id
            ).first()
            if existing:
                print(f"  Transaction already exists for {inv_item.name}, skipping.")
                continue

            # 1. Deduct from Room Stock
            room_stock = db.query(LocationStock).filter(
                LocationStock.location_id == room_loc_id,
                LocationStock.item_id == item_id
            ).first()
            if room_stock:
                room_stock.quantity = max(0, float(room_stock.quantity) - return_qty)
                print(f"  Room stock reduced to {room_stock.quantity}")

            # 2. Add to destination stock
            dest_stock = db.query(LocationStock).filter(
                LocationStock.location_id == return_location_id,
                LocationStock.item_id == item_id
            ).first()
            if dest_stock:
                dest_stock.quantity = float(dest_stock.quantity) + return_qty
            else:
                db.add(LocationStock(
                    location_id=return_location_id,
                    item_id=item_id,
                    quantity=return_qty,
                    last_updated=datetime.utcnow(),
                    branch_id=req.branch_id
                ))
            
            # 3. Create return transaction record
            return_loc = db.query(Location).filter(Location.id == return_location_id).first()
            db.add(InventoryTransaction(
                item_id=item_id,
                transaction_type="transfer_in",
                quantity=return_qty,
                unit_price=inv_item.unit_price or 0.0,
                total_amount=0.0,
                reference_number=f"CHKINV-RET-{req.id}",
                notes=f"Return at checkout (corrective) - Room {req.room_number}",
                created_by=1,
                source_location_id=room_loc_id,
                destination_location_id=return_location_id,
                branch_id=req.branch_id
            ))

            # 4. Zero StockIssueDetail quantities for this item
            issue_details = db.query(StockIssueDetail).join(StockIssue).filter(
                StockIssue.destination_location_id == room_loc_id,
                StockIssueDetail.item_id == item_id
            ).all()
            for d in issue_details:
                d.issued_quantity = 0
            
            # 5. Update global stock if returning to warehouse-like location
            if return_loc and return_loc.location_type and return_loc.location_type.upper() in ["WAREHOUSE", "CENTRAL_WAREHOUSE", "BRANCH_STORE"]:
                inv_item.current_stock = (inv_item.current_stock or 0) + return_qty
                print(f"  Global stock for {inv_item.name} += {return_qty}")

            print(f"  SUCCESS: Returned {return_qty}x {inv_item.name} to '{return_loc.name if return_loc else return_location_id}'")

        db.commit()
        print("\nDone. All corrective returns committed.")

        # Verify
        print("\n--- Verification ---")
        room_stock = db.query(LocationStock).filter(LocationStock.location_id == room_loc_id, LocationStock.item_id == 1).first()
        print(f"  Room 101 stock for TV: {room_stock.quantity if room_stock else 'N/A'}")
        
        dest = db.query(LocationStock).filter(LocationStock.location_id == 3, LocationStock.item_id == 1).first()
        print(f"  qwerty stock for TV: {dest.quantity if dest else 'N/A'}")

        txns = db.query(InventoryTransaction).filter(
            InventoryTransaction.reference_number == f"CHKINV-RET-29"
        ).all()
        print(f"  Transactions created: {len(txns)}")

    except Exception as e:
        db.rollback()
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    fix_missed_return()
