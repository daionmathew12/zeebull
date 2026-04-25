from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys

sys.path.append(r"c:\releasing\New Orchid\ResortApp")
from app.models.expense import Expense

engine = create_engine("postgresql+psycopg2://postgres:qwerty123@localhost:5432/zeebuldb")
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def check_expenses():
    print("Checking Expenses...")
    # Get unique departments
    depts = db.query(Expense.department).distinct().all()
    print(f"Departments in Expense table: {[d[0] for d in depts]}")
    
    # Get all expenses
    exps = db.query(Expense).all()
    print(f"Total expenses: {len(exps)}")
    for e in exps:
        print(f"ID: {e.id}, Amount: {e.amount}, Dept: {e.department}, Desc: {e.description}, Date: {e.date}")

if __name__ == "__main__":
    check_expenses()
