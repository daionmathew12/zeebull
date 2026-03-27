from app.database import SessionLocal
from app.models.inventory import LocationStock

def check_all():
    db = SessionLocal()
    loc_id = 6
    stocks = db.query(LocationStock).filter(LocationStock.location_id == loc_id).all()
    for s in stocks:
        print(f"ID:{s.item_id} | Name:{s.item.name} | Qty:{s.quantity}")
    db.close()

if __name__ == "__main__":
    check_all()
