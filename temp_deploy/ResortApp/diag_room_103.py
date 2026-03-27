from app.database import SessionLocal
from app.models.room import Room
from app.models.inventory import InventoryItem, LocationStock, StockIssue, StockIssueDetail, AssetMapping, AssetRegistry, InventoryCategory
from sqlalchemy.orm import joinedload

def check_room_103_details():
    db = SessionLocal()
    room = db.query(Room).filter(Room.number == '103').first()
    if not room:
        print("Room 103 not found")
        return

    room_loc_id = room.inventory_location_id
    print(f"Room 103 LocID: {room_loc_id}")

    # 1. Check Location Stock
    stocks = db.query(LocationStock).options(joinedload(LocationStock.item)).filter(LocationStock.location_id == room_loc_id).all()
    print("STOCKS:")
    for s in stocks:
        print(f"S|{s.item.name}|{s.item_id}|{s.quantity}")

    # 2. Check All Issues
    issues = db.query(StockIssueDetail).join(StockIssue).options(joinedload(StockIssueDetail.item)).filter(
        StockIssue.destination_location_id == room_loc_id
    ).all()
    print("ISSUES:")
    for d in issues:
        is_rented = (d.rental_price and d.rental_price > 0) or d.is_payable
        print(f"I|{d.item.name}|{d.item_id}|{d.issued_quantity}|{is_rented}|{d.rental_price}")

    # 3. Check Asset Mappings
    mappings = db.query(AssetMapping).options(joinedload(AssetMapping.item)).filter(
        AssetMapping.location_id == room_loc_id, 
        AssetMapping.is_active == True
    ).all()
    print("MAPPINGS:")
    for m in mappings:
        print(f"M|{m.item.name}|{m.item_id}|{m.quantity}|{m.notes}")

    db.close()

if __name__ == "__main__":
    check_room_103_details()
