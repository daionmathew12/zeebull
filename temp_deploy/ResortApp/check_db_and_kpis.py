import sys
import os
import json
from datetime import date
sys.path.append(os.getcwd())

from app.database import SessionLocal, SQLALCHEMY_DATABASE_URL
from app.api.dashboard import get_kpis

def check_kpis():
    print(f"DATABASE_URL in app: {SQLALCHEMY_DATABASE_URL}")
    db = SessionLocal()
    try:
        result = get_kpis(db)
        print(f"KPIs result: {result}")
    finally:
        db.close()

if __name__ == "__main__":
    check_kpis()
