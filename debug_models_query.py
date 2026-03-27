import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), "ResortApp"))
load_dotenv(os.path.join(os.getcwd(), "ResortApp", ".env"))

from app.models.employee import WorkingLog
from sqlalchemy import func

engine = create_engine(os.getenv("DATABASE_URL"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

today = datetime.now().date()
yesterday = today - timedelta(days=1)
branch_id = 2

print(f"Today: {today}, Yesterday: {yesterday}, Branch: {branch_id}")

query_online = db.query(func.count(func.distinct(WorkingLog.employee_id))).filter(
    WorkingLog.check_out_time.is_(None),
    WorkingLog.date >= yesterday
)
if branch_id is not None:
    query_online = query_online.filter(WorkingLog.branch_id == branch_id)

online_count = query_online.scalar() or 0
print(f"Currently Online Count: {online_count}")

# Check individual logs
logs = db.query(WorkingLog).filter(WorkingLog.employee_id == 3).all()
for log in logs:
    print(f"Log: ID={log.id}, Date={log.date}, Out={log.check_out_time}, Branch={log.branch_id}")

db.close()
