
import sys
import os
from sqlalchemy import create_engine, text

# Add root directory to path
sys.path.append(os.getcwd())

from app.database import SQLALCHEMY_DATABASE_URL

def add_bill_details_column():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as conn:
        try:
            print("Attempting to add 'bill_details' column to 'checkouts' table...")
            conn.execute(text("ALTER TABLE checkouts ADD COLUMN bill_details JSON"))
            print("Successfully added 'bill_details' column.")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                print("Column 'bill_details' already exists.")
            else:
                print(f"Error adding column: {e}")

if __name__ == "__main__":
    add_bill_details_column()
