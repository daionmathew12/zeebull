import sys
import os
import json
from datetime import date
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.api.dashboard import get_reports_data

def check_reports():
    db = SessionLocal()
    try:
        result = get_reports_data(db)
        print(f"Reports result: {result}")
        json_str = json.dumps(result, default=str)
        print(f"JSON Length: {len(json_str)}")
    finally:
        db.close()

if __name__ == "__main__":
    check_reports()
