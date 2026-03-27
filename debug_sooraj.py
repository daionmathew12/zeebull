import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), "ResortApp"))
load_dotenv(os.path.join(os.getcwd(), "ResortApp", ".env"))

engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    print("--- Searching for Sooraj ---")
    emps = conn.execute(text("SELECT id, name, user_id FROM employees WHERE name ILIKE '%sooraj%'")).fetchall()
    for emp in emps:
        print(f"Employee: ID={emp.id}, Name={emp.name}, UserID={emp.user_id}")
        user_row = conn.execute(text(f"SELECT * FROM users WHERE id={emp.user_id}")).fetchone()
        if user_row:
            user = dict(user_row._mapping)
            print(f"  User Data: {user}")
            
            # Check Working Log
            log = conn.execute(text(f"SELECT id, check_in_time, check_out_time, date FROM working_logs WHERE employee_id={emp.id} ORDER BY id DESC LIMIT 1")).fetchone()
            if log:
                print(f"  Latest Working Log: ID={log.id}, In={log.check_in_time}, Out={log.check_out_time}, Date={log.date}")
            else:
                print("  No Working Log found.")
            
            # Check Attendance
            att = conn.execute(text(f"SELECT id, status, clock_in, clock_out FROM attendances WHERE user_id={user['id']} ORDER BY id DESC LIMIT 1")).fetchone()
            if att:
                print(f"  Latest Attendance: ID={att.id}, Status={att.status}, ClockIn={att.clock_in}, ClockOut={att.clock_out}")
            else:
                print("  No Attendance found.")
        else:
            print("  No linked user found.")
