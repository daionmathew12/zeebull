import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), "ResortApp"))
load_dotenv(os.path.join(os.getcwd(), "ResortApp", ".env"))

engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("--- Searching for Sooraj working_logs ---")
    logs = conn.execute(text("SELECT * FROM working_logs WHERE employee_id=3 ORDER BY id DESC")).fetchall()
    for log in logs:
        print(dict(log._mapping))
    
    if not logs:
        print("No working logs for Sooraj.")
