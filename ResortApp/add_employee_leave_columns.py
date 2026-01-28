"""Add missing leave balance columns to employees table"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from sqlalchemy import text

def add_leave_balance_columns():
    db = SessionLocal()
    try:
        columns_to_add = [
            ("paid_leave_balance", "INTEGER DEFAULT 12"),
            ("sick_leave_balance", "INTEGER DEFAULT 12"),
            ("long_leave_balance", "INTEGER DEFAULT 5"),
            ("wellness_leave_balance", "INTEGER DEFAULT 5")
        ]
        
        for col_name, col_type in columns_to_add:
            # Check if column exists
            check_query = text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='employees' AND column_name='{col_name}'
            """)
            result = db.execute(check_query).fetchone()
            
            if result:
                print(f"Column '{col_name}' already exists.")
            else:
                # Add the column
                alter_query = text(f"""
                    ALTER TABLE employees 
                    ADD COLUMN {col_name} {col_type}
                """)
                db.execute(alter_query)
                db.commit()
                print(f"Successfully added '{col_name}' column.")
                
        print("\nAll leave balance columns have been added successfully!")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_leave_balance_columns()
