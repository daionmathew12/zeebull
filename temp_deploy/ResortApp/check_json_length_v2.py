import sys
import os
import json
from datetime import date
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.api.employee import _list_employees_impl
from app.models.user import User

class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)

def check_json():
    db = SessionLocal()
    try:
        user = db.query(User).first()
        result = _list_employees_impl(db, user)
        print(f"Number of employees: {len(result)}")
        json_str = json.dumps(result, cls=DateEncoder)
        print(f"JSON Length: {len(json_str)}")
        print(f"JSON Content: {json_str[:200]}...")
    finally:
        db.close()

if __name__ == "__main__":
    check_json()
