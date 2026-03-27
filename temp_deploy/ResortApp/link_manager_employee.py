"""Link manager user to an employee record"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.user import User
from app.models.employee import Employee
from datetime import date

def link_manager_to_employee():
    db = SessionLocal()
    try:
        # Find the manager user
        user = db.query(User).filter(User.email == "m@orchid.com").first()
        
        if not user:
            print("User m@orchid.com not found!")
            return
            
        print(f"Found user: {user.email}, ID: {user.id}")
        
        # Check if employee record exists
        employee = db.query(Employee).filter(Employee.user_id == user.id).first()
        
        if employee:
            print(f"Employee already exists: {employee.name}, ID: {employee.id}")
        else:
            # Create employee record
            new_employee = Employee(
                name="Manager",
                role="manager",
                salary=50000.0,
                join_date=date.today(),
                user_id=user.id,
                paid_leave_balance=12,
                sick_leave_balance=12,
                long_leave_balance=5,
                wellness_leave_balance=5
            )
            db.add(new_employee)
            db.commit()
            db.refresh(new_employee)
            print(f"Created employee record: {new_employee.name}, ID: {new_employee.id}")
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    link_manager_to_employee()
