import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), "ResortApp"))
load_dotenv(os.path.join(os.getcwd(), "ResortApp", ".env"))

engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("--- Detailed check for Sooraj ---")
    emp = conn.execute(text("SELECT id, name, user_id, branch_id FROM employees WHERE id=3")).fetchone()
    if emp:
        print(f"Employee ID: {emp.id}, Name: {emp.name}, UserID: {emp.user_id}, BranchID: {emp.branch_id}")
        user = dict(conn.execute(text(f"SELECT * FROM users WHERE id={emp.user_id}")).fetchone()._mapping)
        print(f"User BranchID: {user['branch_id']}")
        
        print("\n--- Recent working logs ---")
        logs = conn.execute(text("SELECT * FROM working_logs WHERE employee_id=3 ORDER BY id DESC")).fetchall()
        for log in logs:
            print(dict(log._mapping))
            
    print("\n--- Current active branch in Dashboard? ---")
    # Usually determined by current user's branch or selected branch. 
    # Let's see all branches.
    branches = conn.execute(text("SELECT id, name FROM branches")).fetchall()
    for b in branches:
        print(f"Branch: ID={b.id}, Name={b.name}")
