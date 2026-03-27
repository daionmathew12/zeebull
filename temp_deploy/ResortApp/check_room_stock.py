from app.database import SessionLocal
from app.models.room import Room
from app.models.inventory import StockIssue, StockIssueDetail, InventoryItem
import json

def check_room_stock():
    db = SessionLocal()
    room = db.query(Room).filter(Room.number == '102').first()
    if not room:
        print("Room 102 not found")
        return

    print(f"Room 102 id: {room.id}, loc_id: {room.inventory_location_id}")
    
    issues = db.query(StockIssue).join(StockIssueDetail).filter(
        StockIssue.destination_location_id == room.inventory_location_id
    ).all()
    
    result = []
    for issue in issues:
        for detail in issue.details:
            result.append({
                "item_name": detail.item.name if detail.item else "N/A",
                "item_id": detail.item_id,
                "qty": detail.issued_quantity,
                "rental_price": detail.rental_price,
                "is_payable": detail.is_payable,
                "issue_date": str(issue.issue_date)
            })
    
    print(json.dumps(result, indent=2))
    db.close()

if __name__ == "__main__":
    check_room_stock()
