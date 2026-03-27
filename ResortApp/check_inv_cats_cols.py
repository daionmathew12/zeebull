from sqlalchemy import create_engine, text
from app.database import SQLALCHEMY_DATABASE_URL
import os

def check_columns():
    print(f"Checking database: {SQLALCHEMY_DATABASE_URL}")
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'inventory_categories'"))
        columns = [row[0] for row in result]
        print("Columns in inventory_categories table:", columns)
        
        if 'parent_department' in columns:
            print("✅ parent_department column exists")
        else:
            print("❌ parent_department column MISSING")

if __name__ == "__main__":
    check_columns()
