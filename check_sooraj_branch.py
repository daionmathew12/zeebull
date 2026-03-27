import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), "ResortApp"))
load_dotenv(os.path.join(os.getcwd(), "ResortApp", ".env"))

engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    # Check Sooraj's employee info
    res = conn.execute(text("SELECT id, name, branch_id FROM employees WHERE id = 2"))
    for row in res:
        print(f"Employee: ID={row.id}, Name={row.name}, Branch={row.branch_id}")
        
    # Check ALL working logs for this employee
    res = conn.execute(text("SELECT id, employee_id, branch_id, date, check_out_time FROM working_logs WHERE employee_id = 2"))
    for row in res:
        print(f"Log: ID={row.id}, Branch={row.branch_id}, Date={row.date}, Out={row.check_out_time}")
        
    # Check current status of branch 2
    res = conn.execute(text("SELECT id, name FROM branches WHERE id = 2"))
    for row in res:
        print(f"Branch: ID={row.id}, Name={row.name}")
