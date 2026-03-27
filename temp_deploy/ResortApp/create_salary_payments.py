"""
Script to update employee salary and create sample payment history
Run this to populate salary data for testing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Employee, SalaryPayment
from datetime import date, datetime

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import SessionLocal, engine
from app.models import Employee, SalaryPayment
from datetime import date, datetime

def run_migration(db):
    """Ensure database schema is up to date"""
    print("🔄 Checking database schema (PostgreSQL Only)...")
    
    # 1. Add user_id to employees if missing
    try:
        db.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id)"))
        print("  ✓ user_id column check passed")
    except Exception as e:
        print(f"  ℹ Note on user_id: {e}")

    # 2. Add leave balance columns if missing
    for col in ['paid_leave_balance', 'sick_leave_balance', 'long_leave_balance', 'wellness_leave_balance']:
        try:
            db.execute(text(f"ALTER TABLE employees ADD COLUMN IF NOT EXISTS {col} INTEGER DEFAULT 12"))
            print(f"  ✓ {col} column check passed")
        except Exception as e:
            print(f"  ℹ Note on {col}: {e}")

    # 3. Create SalaryPayments table
    try:
        # Check if table exists
        check = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_name = 'salary_payments'")).fetchone()
            
        if not check:
            print("  creating salary_payments table...")
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS salary_payments (
                    id SERIAL PRIMARY KEY,
                    employee_id INTEGER NOT NULL REFERENCES employees(id),
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
            print("  ✓ Created salary_payments table")
        else:
            print("  ✓ salary_payments table already exists")
            
        db.commit()
            
    except Exception as e:
        print(f"  ⚠️ Migration warning: {e}")
        db.rollback()

def create_salary_payments():
    """Create sample salary payment records for all employees"""
    db = SessionLocal()
    
    # Run migration first
    run_migration(db)
    
    try:
        # Get all employees
        employees = db.query(Employee).all()
        
        if not employees:
            print("No employees found!")
            return
        
        for employee in employees:
            print(f"\nProcessing employee: {employee.name} (ID: {employee.id})")
            
            # Update salary if it's 0 or None
            if not employee.salary or employee.salary == 0:
                employee.salary = 25000.0  # Default salary
                print(f"  ✓ Updated salary to ₹{employee.salary}")
            
            # Check if payment records already exist
            existing_payments = db.query(SalaryPayment).filter(
                SalaryPayment.employee_id == employee.id
            ).count()
            
            if existing_payments > 0:
                print(f"  ℹ Already has {existing_payments} payment record(s)")
                continue
            
            # Create payment records for last 3 months
            months = [
                ("December 2025", 2025, 12, date(2026, 1, 1)),
                ("November 2025", 2025, 11, date(2025, 12, 1)),
                ("October 2025", 2025, 10, date(2025, 11, 1)),
            ]
            
            for month_name, year, month_num, payment_date in months:
                payment = SalaryPayment(
                    employee_id=employee.id,
                    month=month_name,
                    year=year,
                    month_number=month_num,
                    basic_salary=employee.salary,
                    allowances=2000.0,  # Sample allowance
                    deductions=1500.0,  # Sample deduction
                    net_salary=employee.salary + 2000.0 - 1500.0,
                    payment_date=payment_date,
                    payment_method="bank_transfer",
                    payment_status="paid",
                    notes=f"Salary for {month_name}"
                )
                db.add(payment)
                print(f"  ✓ Created payment record for {month_name}")
            
        db.commit()
        print("\n✅ Successfully created salary payment records!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Creating salary payment records...")
    print("=" * 50)
    create_salary_payments()
