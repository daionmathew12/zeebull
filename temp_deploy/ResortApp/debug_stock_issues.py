from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, joinedload
from app.models.inventory import StockIssue, StockIssueDetail, InventoryItem, Location
from app.models.room import Room
from app.database import Base
import os
from dotenv import load_dotenv

load_dotenv()

# Database Setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def debug_stock_issues(room_number):
    print(f"--- Debugging Stock Issues for Room {room_number} ---")
    room = db.query(Room).filter(Room.number == room_number).first()
    if not room:
        print(f"Room {room_number} not found.")
        return
    
    loc_id = room.inventory_location_id
    if not loc_id:
        print(f"Room {room_number} has no inventory_location_id.")
        return
        
    print(f"Location ID: {loc_id}")
    
    issues = db.query(StockIssue).filter(StockIssue.destination_location_id == loc_id).all()
    
    print(f"Found {len(issues)} stock issues.")
    
    all_details = []
    
    for issue in issues:
        print(f"\nIssue #{issue.id} ({issue.issue_number}) Date: {issue.issue_date}")
        for detail in issue.details:
            item_name = detail.item.name if detail.item else "Unknown"
            print(f"  - Item: {item_name} (ID: {detail.item_id})")
            print(f"    Qty: {detail.issued_quantity} {detail.unit}")
            print(f"    Payable: {detail.is_payable}")
            print(f"    Unit Price: {detail.unit_price}")
            print(f"    Notes: {detail.notes}")
            all_details.append(detail)

    print("\n--- Summary of 'Mineral Water' ---")
    mw_details = [d for d in all_details if "mineral" in (d.item.name.lower() if d.item else "")]
    for d in mw_details:
        print(f"ID: {d.id} | Qty: {d.issued_quantity} | Payable: {d.is_payable}")
        
if __name__ == "__main__":
    debug_stock_issues("104")
