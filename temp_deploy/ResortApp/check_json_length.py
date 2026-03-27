import sys
import os
import json
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.api.employee import _list_employees_impl
from app.models.user import User

def check_json():
    db = SessionLocal()
    try:
        # Mock a user if needed, but _list_employees_impl doesn't use current_user fields deeply
        user = db.query(User).first()
        result = _list_employees_impl(db, user)
        print(f"Number of employees: {len(result)}")
        json_str = json.dumps(result)
        print(f"JSON Length: {len(json_str)}")
        print(f"JSON Content: {json_str[:200]}...")
    finally:
        db.close()

if __name__ == "__main__":
    check_json()
