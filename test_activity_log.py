import os
import sys

# Force UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add the project root to sys.path
sys.path.append(os.path.join(os.getcwd(), "ResortApp"))

from app.database import SessionLocal
from app.models.activity_log import ActivityLog
from datetime import datetime

def test_log():
    db = SessionLocal()
    try:
        log = ActivityLog(
            action="Test Action",
            method="GET",
            path="/api/test",
            status_code=200,
            client_ip="127.0.0.1",
            details="Test details",
            branch_id=1
        )
        db.add(log)
        db.commit()
        print("Success: Log inserted successfully.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    test_log()
