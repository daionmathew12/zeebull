from app.database import SessionLocal
from app.models.booking import Room

def check_loc():
    db = SessionLocal()
    r = db.query(Room).filter(Room.number == "103").first()
    print(f"Room 103 | ID:{r.id} | LocID:{r.inventory_location_id}")
    db.close()

if __name__ == "__main__":
    check_loc()
