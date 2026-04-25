from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from datetime import date, datetime
import sys
import os

sys.path.append(r"c:\releasing\New Orchid\ResortApp")

from app.database import Base
from app.models.foodorder import FoodOrder

# Use the real DB to see what's going on
from app.utils.auth import get_db

# Mocking db session for script
from sqlalchemy import create_engine
engine = create_engine("postgresql+psycopg2://postgres:qwerty123@localhost:5432/zeebuldb")
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def dump_orders():
    print("Dumping Food Orders...")
    orders = db.query(FoodOrder).all()
    print(f"Total orders: {len(orders)}")
    for o in orders:
        print(f"ID: {o.id}, Amount: {o.amount}, Total w/ GST: {o.total_with_gst}, Status: {o.status}, Created: {o.created_at}")
        try:
            print(f"  Room: {o.room.number if o.room else 'None'}")
        except Exception as e:
            print(f"  ERROR accessing room: {e}")

if __name__ == "__main__":
    dump_orders()
