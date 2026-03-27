from app.database import SessionLocal
from app.models.room import Room
from app.models.inventory import InventoryItem, LocationStock, StockIssue, StockIssueDetail, AssetMapping, InventoryTransaction
from sqlalchemy import or_

def check_room_103_history():
    db = SessionLocal()
    room = db.query(Room).filter(Room.number == '103').first()
    loc_id = room.inventory_location_id
    
    print(f"Room 103 LocID: {loc_id}")
    
    for item_id in [3, 4]: # LED, TV
        item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        print(f"\nITEM: {item.name} (ID: {item_id})")
        
        # Stock
        stock = db.query(LocationStock).filter(LocationStock.location_id == loc_id, LocationStock.item_id == item_id).first()
        print(f"Current Location Stock: {stock.quantity if stock else 0}")
        
        # Transactions
        txns = db.query(InventoryTransaction).filter(
            InventoryTransaction.item_id == item_id,
            or_(InventoryTransaction.reference_number.ilike(f"%RM-{room.number}%"), 
                InventoryTransaction.notes.ilike(f"%Room {room.number}%"))
        ).all()
        print("Recent Transactions:")
        for t in txns:
            print(f"  {t.transaction_type} | {t.quantity} | {t.reference_number} | {t.notes}")
            
        # Issues
        issues = db.query(StockIssueDetail).join(StockIssue).filter(
            StockIssue.destination_location_id == loc_id,
            StockIssueDetail.item_id == item_id
        ).all()
        print("Issues:")
        for d in issues:
            is_rented = (d.rental_price and d.rental_price > 0) or d.is_payable
            print(f"  ID: {d.id} | Qty: {d.issued_quantity} | Rented: {is_rented} | Damaged: {d.is_damaged}")
            
        # Mappings
        mappings = db.query(AssetMapping).filter(AssetMapping.location_id == loc_id, AssetMapping.item_id == item_id).all()
        print("Mappings:")
        for m in mappings:
            print(f"  ID: {m.id} | Qty: {m.quantity} | Active: {m.is_active} | Notes: {m.notes}")

    db.close()

if __name__ == "__main__":
    check_room_103_history()
