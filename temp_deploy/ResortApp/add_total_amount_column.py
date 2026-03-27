"""
Simple script to add total_amount column to package_bookings table
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from sqlalchemy import text

def add_total_amount_column():
    db = SessionLocal()
    try:
        # Check if column already exists
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='package_bookings' AND column_name='total_amount'
        """)
        result = db.execute(check_query).fetchone()
        
        if result:
            print("Column 'total_amount' already exists in 'package_bookings' table.")
        else:
            # Add the column
            alter_query = text("""
                ALTER TABLE package_bookings 
                ADD COLUMN total_amount FLOAT DEFAULT 0.0
            """)
            db.execute(alter_query)
            db.commit()
            print("Successfully added 'total_amount' column to 'package_bookings' table.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_total_amount_column()
