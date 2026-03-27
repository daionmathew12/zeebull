import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), "ResortApp"))
load_dotenv(os.path.join(os.getcwd(), "ResortApp", ".env"))

engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    res = conn.execute(text("SELECT id, employee_id, branch_id, date, check_out_time FROM working_logs WHERE date='2026-03-14'"))
    for row in res:
        print(f"ID: {row.id}, Employee: {row.employee_id}, Branch: {row.branch_id}, Date: {row.date}, Out: {row.check_out_time}")
