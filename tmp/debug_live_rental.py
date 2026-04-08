import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ResortApp')))

from app.database import SessionLocal
from app.models.checkout import CheckoutRequest
from app.models.inventory import StockIssue, StockIssueDetail, LocationStock, Location
from app.models.room import Room
import json

def debug_latest_checkout():
    db = SessionLocal()
    try:
        req = db.query(CheckoutRequest).filter(CheckoutRequest.room_number == "101").order_by(CheckoutRequest.id.desc()).first()
        if not req:
            print("No checkout request found for room 101.")
            return

        print(f"Latest Request ID: {req.id}, Room: {req.room_number}, Status: {req.status}")
        print(f"Inventory Data: {json.dumps(req.inventory_data, indent=2) if req.inventory_data else 'None'}")

        room = db.query(Room).filter(Room.number == req.room_number).first()
        if room:
            print(f"\n--- Location Stock for Room {req.room_number} (Loc ID: {room.inventory_location_id}) ---")
            stocks = db.query(LocationStock).filter(LocationStock.location_id == room.inventory_location_id).all()
            for s in stocks:
                item_name = s.item.name if s.item else s.item_id
                print(f"Room Stock -> Item: {item_name}, Qty: {s.quantity}")

            print(f"\n--- Stock Issues for Room {req.room_number} ---")
            issues = db.query(StockIssueDetail).join(StockIssue).filter(StockIssue.destination_location_id == room.inventory_location_id).all()
            for i in issues:
                item_name = i.item.name if i.item else i.item_id
                print(f"Issued -> Item: {item_name}, Qty: {i.issued_quantity}, Rent: {i.rental_price}")
        
    finally:
        db.close()

if __name__ == "__main__":
    debug_latest_checkout()
