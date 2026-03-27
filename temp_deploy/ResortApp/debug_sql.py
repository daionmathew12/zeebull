import sys
import os
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.room import Room
from sqlalchemy import func
import logging

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

def debug():
    db = SessionLocal()
    try:
        print("Starting query...")
        count = db.query(func.count(Room.id)).scalar()
        print(f"Room count via ORM: {count}")
    finally:
        db.close()

if __name__ == "__main__":
    debug()
