from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys

sys.path.append(r"c:\releasing\New Orchid\ResortApp")
from app.models.checkout import Checkout

engine = create_engine("postgresql+psycopg2://postgres:qwerty123@localhost:5432/zeebuldb")
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def check_checkouts():
    print("Checking Checkouts...")
    chks = db.query(Checkout).all()
    print(f"Total checkouts: {len(chks)}")
    for c in chks:
        print(f"ID: {c.id}, Room: {c.room_number}, Total: {c.room_total}, Status: {c.payment_status}, Date: {c.checkout_date}")

if __name__ == "__main__":
    check_checkouts()
