import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), "ResortApp"))
load_dotenv(os.path.join(os.getcwd(), "ResortApp", ".env"))

engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    conn.execute(text("UPDATE working_logs SET branch_id=2 WHERE employee_id=3 AND date='2026-03-14'"))
    conn.commit()
    print("Updated Sooraj working log to branch 2")
