import sys
import os
import json
from datetime import date, datetime
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.api.employee import get_salary_payments
from app.models.user import User

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)

def check_payments():
    db = SessionLocal()
    try:
        # Mock user
        user = db.query(User).filter(User.id == 27).first() # User 27 is Basil/alphi
        result = get_salary_payments(4, db, user)
        print(f"Number of payments: {len(result)}")
        json_str = json.dumps(result, cls=DateTimeEncoder)
        print(f"JSON Length: {len(json_str)}")
        print(f"JSON Content: {json_str}")
    finally:
        db.close()

if __name__ == "__main__":
    check_payments()
