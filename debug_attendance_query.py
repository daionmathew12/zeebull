import os
import sys
from sqlalchemy import create_engine, text, func
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), "ResortApp"))
load_dotenv(os.path.join(os.getcwd(), "ResortApp", ".env"))

engine = create_engine(os.getenv("DATABASE_URL"))

ist = pytz.timezone('Asia/Kolkata')
now_ist = datetime.now(ist)
today = now_ist.date()
yesterday = today - timedelta(days=1)
branch_id = 2

with engine.connect() as conn:
    print(f"Today: {today}, Yesterday: {yesterday}, Branch: {branch_id}")
    
    # Check Sooraj's specific log
    res = conn.execute(text("""
        SELECT id, employee_id, branch_id, date, check_in_time, check_out_time
        FROM working_logs
        WHERE employee_id = 2
    """))
    for row in res:
        print(f"Log: ID={row.id}, Emp={row.employee_id}, Branch={row.branch_id}, Date={row.date}, In={row.check_in_time}, Out={row.check_out_time}")
        
    # Run the equivalent online count query
    res = conn.execute(text("""
        SELECT count(DISTINCT employee_id)
        FROM working_logs
        WHERE check_out_time IS NULL
        AND date >= :yesterday
        AND branch_id = :branch_id
    """), {"yesterday": yesterday, "branch_id": branch_id})
    count = res.scalar()
    print(f"Online Count (SQL): {count}")
