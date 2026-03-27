from sqlalchemy import create_engine, text
from app.database import SQLALCHEMY_DATABASE_URL

def migrate_database():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as conn:
        # 1. Create SalaryPayment table
        print("Creating salary_payments table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS salary_payments (
                id SERIAL PRIMARY KEY,
                employee_id INTEGER REFERENCES employees(id),
                month VARCHAR NOT NULL,
                year INTEGER NOT NULL,
                month_number INTEGER NOT NULL,
                basic_salary FLOAT NOT NULL,
                allowances FLOAT DEFAULT 0.0,
                deductions FLOAT DEFAULT 0.0,
                net_salary FLOAT NOT NULL,
                payment_date DATE,
                payment_method VARCHAR,
                payment_status VARCHAR DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes VARCHAR
            )
        """))
        
        # 2. Add user_id column to employees table if it doesn't exist
        print("Checking for user_id column in employees table...")
        try:
            conn.execute(text("ALTER TABLE employees ADD COLUMN user_id INTEGER REFERENCES users(id)"))
            print("  ✓ Added user_id column")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("  ✓ user_id column already exists")
            else:
                print(f"  ℹ Note: {e}")

        # 3. Add image_url column if it doesn't exist (renaming/adding)
        print("Checking for image_url column in employees table...")
        try:
            conn.execute(text("ALTER TABLE employees ADD COLUMN image_url VARCHAR"))
            print("  ✓ Added image_url column")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("  ✓ image_url column already exists")
            else:
                print(f"  ℹ Note: {e}")
                
        # 4. Add leave balance columns if they don't exist
        print("Checking for leave balance columns...")
        for col in ['paid_leave_balance', 'sick_leave_balance', 'long_leave_balance', 'wellness_leave_balance']:
            try:
                conn.execute(text(f"ALTER TABLE employees ADD COLUMN {col} INTEGER DEFAULT 12"))
                print(f"  ✓ Added {col} column")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print(f"  ✓ {col} column already exists")
                else:
                    print(f"  ℹ Note: {e}")
                    
        conn.commit()
        print("\n✅ Database migration completed successfully!")

if __name__ == "__main__":
    migrate_database()
