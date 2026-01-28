"""Check if employee leave columns exist"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from sqlalchemy import text

def check_employee_columns():
    db = SessionLocal()
    try:
        query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='employees'
            ORDER BY ordinal_position
        """)
        result = db.execute(query).fetchall()
        
        print("Columns in 'employees' table:")
        for row in result:
            print(f"  - {row[0]}")
            
        # Check for specific columns
        columns = [r[0] for r in result]
        required_columns = ['paid_leave_balance', 'sick_leave_balance', 'long_leave_balance', 'wellness_leave_balance']
        
        print("\nChecking for leave balance columns:")
        for col in required_columns:
            if col in columns:
                print(f"  ✓ {col} exists")
            else:
                print(f"  ✗ {col} MISSING")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_employee_columns()
