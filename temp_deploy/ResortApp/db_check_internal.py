import sys
import os
# Add the app directory to sys.path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.employee import Employee

def check_db():
    db = SessionLocal()
    try:
        count = db.query(Employee).count()
        print(f"Employee Count in DB: {count}")
        all_emps = db.query(Employee).all()
        for e in all_emps:
            print(f"ID: {e.id}, Name: {e.name}, Role: {e.role}")
    finally:
        db.close()

if __name__ == "__main__":
    check_db()
