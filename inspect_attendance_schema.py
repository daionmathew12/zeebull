import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), "ResortApp"))
load_dotenv(os.path.join(os.getcwd(), "ResortApp", ".env"))

engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    for table in ["users", "employees", "working_logs", "attendances"]:
        print(f"--- Table: {table} ---")
        try:
            res = conn.execute(text(f"SELECT * FROM {table} LIMIT 1")).fetchone()
            if res:
                print(list(res._mapping.keys()))
            else:
                # Get columns from information_schema
                cols = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'")).fetchall()
                print([c[0] for c in cols])
        except Exception as e:
            print(f"Error: {e}")
