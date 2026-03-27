import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), "ResortApp"))
load_dotenv(os.path.join(os.getcwd(), "ResortApp", ".env"))

db_url = os.getenv("DATABASE_URL")
print(f"Using DB: {db_url}")
engine = create_engine(db_url)

with engine.connect() as conn:
    print("--- Searching for Sooraj working_logs ---")
    res = conn.execute(text("SELECT * FROM working_logs WHERE employee_id=3 ORDER BY id DESC"))
    for row in res:
        data = dict(row._mapping)
        print(f"ID: {data['id']}, Branch: {data['branch_id']}, Date: {data['date']}, Out: {data['check_out_time']}")
