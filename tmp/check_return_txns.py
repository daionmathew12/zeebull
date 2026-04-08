import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ResortApp')))

from app.database import SessionLocal
from app.models.checkout import CheckoutRequest
from app.models.inventory import InventoryTransaction, LocationStock, Location, StockIssueDetail, StockIssue
from app.models.room import Room
from sqlalchemy.orm import joinedload

def check_transactions():
    db = SessionLocal()
    try:
        req = db.query(CheckoutRequest).filter(CheckoutRequest.room_number == "101").order_by(CheckoutRequest.id.desc()).first()
        if not req:
            print("No checkout request found for room 101.")
            return

        print(f"CheckoutRequest ID: {req.id}, Room: {req.room_number}, Status: {req.status}")
        print(f"Return location in inventory_data:")
        if req.inventory_data:
            for d in req.inventory_data:
                print(f"  item_id={d.get('item_id')}, is_rentable={d.get('is_rentable')}, return_location_id={d.get('return_location_id')}, allocated_stock={d.get('allocated_stock')}")

        print(f"\n--- InventoryTransactions for checkout ref CHKINV-{req.id} ---")
        txns = db.query(InventoryTransaction).filter(
            InventoryTransaction.reference_number.like(f"%CHKINV-{req.id}%")
        ).all()
        
        if txns:
            for t in txns:
                item_name = t.item.name if t.item else t.item_id
                src = db.query(Location).filter(Location.id == t.source_location_id).first()
                dst = db.query(Location).filter(Location.id == t.destination_location_id).first()
                print(f"  [{t.transaction_type.upper()}] {item_name} x{t.quantity} | From: {src.name if src else t.source_location_id} -> To: {dst.name if dst else t.destination_location_id}")
        else:
            print("  No transactions found for this checkout ref!")

        # Check current stock levels at all locations for item_id=1 (tv)
        print(f"\n--- Current LocationStock for item 'tv' (ID=1) ---")
        stocks = db.query(LocationStock).filter(LocationStock.item_id == 1).all()
        for s in stocks:
            loc = db.query(Location).filter(Location.id == s.location_id).first()
            print(f"  Location: {loc.name if loc else s.location_id}, Qty: {s.quantity}")

        # Also check StockIssueDetails - have they been zeroed?
        room = db.query(Room).filter(Room.number == "101").first()
        if room:
            print(f"\n--- StockIssueDetails for Room 101 (Loc {room.inventory_location_id}) ---")
            issues = db.query(StockIssueDetail).join(StockIssue).filter(
                StockIssue.destination_location_id == room.inventory_location_id,
                StockIssueDetail.item_id == 1
            ).all()
            for i in issues:
                print(f"  IssueDetail ID={i.id}: issued_qty={i.issued_quantity}, rental_price={i.rental_price}")

    finally:
        db.close()

if __name__ == "__main__":
    check_transactions()
