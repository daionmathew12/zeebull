import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), "ResortApp"))
load_dotenv(os.path.join(os.getcwd(), "ResortApp", ".env"))

engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("--- Columns in system_settings ---")
    res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'system_settings'"))
    for row in res:
        print(row.column_name)
