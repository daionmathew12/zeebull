import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), "ResortApp"))
load_dotenv(os.path.join(os.getcwd(), "ResortApp", ".env"))

engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("--- Selecting from system_settings ---")
    try:
        res = conn.execute(text("SELECT id, key, branch_id FROM system_settings"))
        for row in res:
            print(f"ID: {row.id}, Key: {row.key}, Branch: {row.branch_id}")
    except Exception as e:
        print(f"Error: {e}")
