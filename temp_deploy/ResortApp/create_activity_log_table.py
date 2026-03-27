import sys
import os
sys.path.append(os.getcwd())
from app.database import engine, Base
from app.models.activity_log import ActivityLog

def create_table():
    print("Creating activity_logs table...")
    ActivityLog.__table__.create(bind=engine, checkfirst=True)
    print("Done.")

if __name__ == "__main__":
    create_table()
