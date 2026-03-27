import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), "ResortApp"))
load_dotenv(os.path.join(os.getcwd(), "ResortApp", ".env"))

engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("--- Branches ---")
    res = conn.execute(text("SELECT id, name FROM branches"))
    for row in res:
        print(f"ID: {row.id}, Name: {row.name}")
