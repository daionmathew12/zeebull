import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), "ResortApp"))
load_dotenv(os.path.join(os.getcwd(), "ResortApp", ".env"))

engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("--- All Users ---")
    res = conn.execute(text("SELECT id, name, email, branch_id, is_superadmin FROM users"))
    for row in res:
        print(f"ID: {row.id}, Name: {row.name}, Email: {row.email}, Branch: {row.branch_id}, Super: {row.is_superadmin}")
