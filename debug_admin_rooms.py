import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), "ResortApp"))
load_dotenv(os.path.join(os.getcwd(), "ResortApp", ".env"))

engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("--- All Rooms with number 101 ---")
    res = conn.execute(text("SELECT id, number, branch_id, status FROM rooms WHERE number='101'"))
    for row in res:
        print(f"ID: {row.id}, Number: {row.number}, Branch: {row.branch_id}, Status: {row.status}")
    
    print("\n--- Admin User Info ---")
    res = conn.execute(text("SELECT id, name, email, branch_id, is_superadmin FROM users WHERE name='admin' OR email='admin@example.com'"))
    for row in res:
        print(f"ID: {row.id}, Name: {row.name}, Email: {row.email}, Branch: {row.branch_id}, Super: {row.is_superadmin}")
