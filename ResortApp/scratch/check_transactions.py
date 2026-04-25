from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys

sys.path.append(r"c:\releasing\New Orchid\ResortApp")
from app.models.inventory import InventoryTransaction

engine = create_engine("postgresql+psycopg2://postgres:qwerty123@localhost:5432/zeebuldb")
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def check_transactions():
    print("Checking Inventory Transactions...")
    trans = db.query(InventoryTransaction).all()
    print(f"Total transactions: {len(trans)}")
    for t in trans:
        print(f"ID: {t.id}, Type: {t.transaction_type}, Dept: {t.department}, Amount: {t.total_amount}, Created: {t.created_at}")

if __name__ == "__main__":
    check_transactions()
