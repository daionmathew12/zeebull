from sqlalchemy import create_engine, text
import os

def check_data():
    # Attempt to find the URL again or use the known one if hardcoded for debug
    db_url = "postgresql+psycopg2://orchid_user:admin123@localhost/orchid_resort"
    # Note: DB name in migration log was 'orchid_resort', not 'orchid_resort_db'. Changing both.
    
    # Try reading from .env if needed, but let's use the one we believe is correct first
    # Or use the same logic as start_server.py
    
    print(f"Connecting to {db_url}...")
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            # Check employees
            print("--- Employees ---")
            result = conn.execute(text("SELECT id, name, salary FROM employees ORDER BY id"))
            employees = result.fetchall()
            for e in employees:
                print(e)
                
            # Check payments
            print("\n--- Payments ---")
            result = conn.execute(text("SELECT id, employee_id, month, net_salary FROM salary_payments ORDER BY id DESC LIMIT 10"))
            payments = result.fetchall()
            if not payments:
                print("No payments found!")
            for p in payments:
                print(p)
                
            # Check specifically for ID 4
            print("\n--- Check ID 4 ---")
            result = conn.execute(text("SELECT * FROM salary_payments WHERE employee_id = 4"))
            p4 = result.fetchall()
            print(f"Payments for employee 4: {len(p4)}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_data()
