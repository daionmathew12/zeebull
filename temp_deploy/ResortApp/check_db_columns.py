from sqlalchemy import create_engine, text
from app.database import SQLALCHEMY_DATABASE_URL
import os

def check_columns():
    print(f"Checking database: {SQLALCHEMY_DATABASE_URL}")
    if "sqlite" in SQLALCHEMY_DATABASE_URL:
        print("⚠️ WARNING: Using SQLite database! This might be why columns are missing if prod is Postgres.")
        
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'employees'"))
        columns = [row[0] for row in result]
        print("Columns in employees table:", columns)
        
        if 'user_id' in columns:
            print("✅ user_id column exists")
        else:
            print("❌ user_id column MISSING")
            
        # Check salary_payments table too
        try:
            result = conn.execute(text("SELECT count(*) FROM salary_payments"))
            count = result.scalar()
            print(f"✅ salary_payments table exists with {count} records")
        except Exception as e:
            print(f"❌ salary_payments table check failed: {e}")

if __name__ == "__main__":
    check_columns()
