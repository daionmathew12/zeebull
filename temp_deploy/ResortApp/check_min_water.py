from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.inventory import StockIssue
from app.models.room import Room
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

room = db.query(Room).filter(Room.number == "104").first()
loc_id = room.inventory_location_id

print(f"Room 104 Location: {loc_id}")
issues = db.query(StockIssue).filter(StockIssue.destination_location_id == loc_id).all()
for issue in issues:
    for d in issue.details:
        if d.item and "mineral" in d.item.name.lower():
             print(f"StockIssueDetail ID: {d.id} | Qty: {d.issued_quantity} | Payable: {d.is_payable} | Unit Price: {d.unit_price}")
