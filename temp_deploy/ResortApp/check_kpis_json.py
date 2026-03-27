import sys
import os
import json
from datetime import date
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.api.dashboard import get_kpis

def check_kpis():
    db = SessionLocal()
    try:
        result = get_kpis(db)
        print(f"KPIs result: {result}")
        json_str = json.dumps(result)
        print(f"JSON Length: {len(json_str)}")
    finally:
        db.close()

if __name__ == "__main__":
    check_kpis()
