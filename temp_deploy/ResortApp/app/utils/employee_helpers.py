from sqlalchemy.orm import Session
from app.models.employee import Employee
from typing import Optional

def get_fallback_employee_id(db: Session, current_user_employee_id: Optional[int] = None) -> int:
    """
    Returns a valid employee ID. 
    1. Returns current_user_employee_id if provided.
    2. Tries to find employee with ID 1.
    3. Finds the first available employee in the database.
    4. Defaults to 1 if no employees found (will still fail FK, but better than nothing).
    """
    if current_user_employee_id:
        return current_user_employee_id
    
    # Try ID 1
    emp_1 = db.query(Employee).filter(Employee.id == 1).first()
    if emp_1:
        return 1
    
    # Try first employee
    first_emp = db.query(Employee).order_by(Employee.id.asc()).first()
    if first_emp:
        return first_emp.id
    
    # Absolute fallback
    return 1
