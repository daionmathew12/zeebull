import sys
import os
import json
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.api.employee import get_employee
from app.models.user import User

def check():
    db = SessionLocal()
    try:
        user = db.query(User).first()
        res = get_employee(4, db, user)
        print(f"Employee 4 Data: {res}")
    finally:
        db.close()

if __name__ == "__main__":
    check()
