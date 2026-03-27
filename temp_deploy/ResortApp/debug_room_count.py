import sys
import os
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.room import Room
from sqlalchemy import func

def debug():
    db = SessionLocal()
    try:
        count = db.query(func.count(Room.id)).scalar()
        print(f"Room count via ORM: {count}")
        rooms = db.query(Room).all()
        print(f"Actual rooms list: {rooms}")
    finally:
        db.close()

if __name__ == "__main__":
    debug()
