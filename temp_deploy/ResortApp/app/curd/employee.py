from datetime import date
from sqlalchemy.orm import Session
from app.models.user import Role, User
from app.models.employee import Employee, Leave
from app.schemas.employee import EmployeeCreate, LeaveCreate

def create_employee(db: Session, emp: EmployeeCreate):
    employee = Employee(**emp.dict())
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee
def get_role_by_name(db: Session, role_name: str):
    return db.query(Role).filter(Role.name == role_name).first()

def get_employees(db: Session, branch_id=None, skip: int = 0, limit: int = 100):
    q = db.query(Employee)
    if branch_id is not None:
        q = q.filter(Employee.branch_id == branch_id)
    return q.offset(skip).limit(limit).all()


def create_employee(
    db: Session,
    name: str,
    role: str,
    salary: float,
    join_date: date,
):
    db_employee = Employee(
        name=name,
        role=role,
        salary=salary,
        join_date=join_date,
    )
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)

def create_leave(db: Session, leave: LeaveCreate):
    # Use model_dump() for Pydantic v2, or dict() for v1
    leave_data = leave.model_dump() if hasattr(leave, 'model_dump') else leave.dict()
    # Ensure leave_type is included if provided, otherwise it uses the model's default
    leave_entry = Leave(**leave_data)
    db.add(leave_entry)
    db.commit()
    db.refresh(leave_entry)
    return leave_entry

def get_employee_leaves(db: Session, emp_id: int, skip: int = 0, limit: int = 100):
    return db.query(Leave).filter(Leave.employee_id == emp_id).offset(skip).limit(limit).all()

def update_leave_status(db: Session, leave_id: int, status: str):
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if leave:
        leave.status = status
        db.commit()
        db.refresh(leave)
    return leave
def create_employee_with_image(
    db: Session,
    name: str,
    role: str,
    salary: float,
    join_date: str,
    # ✅ Changed from image to image_url
    image_url: str,
    user_id: int,
    # Leave balances with defaults
    paid_leave_balance: int = 12,
    sick_leave_balance: int = 12,
    long_leave_balance: int = 5,
    wellness_leave_balance: int = 5,
    daily_tasks: str = None,
    branch_id: int = None,
):

    # This part of the code is responsible for creating the new Employee object.
    new_employee = Employee(
        name=name,
        role=role,
        salary=salary,
        join_date=join_date,
        # ✅ Pass image_url to the correct model field
        image_url=image_url,
        user_id=user_id,
        paid_leave_balance=paid_leave_balance,
        sick_leave_balance=sick_leave_balance,
        long_leave_balance=long_leave_balance,
        wellness_leave_balance=wellness_leave_balance,
        daily_tasks=daily_tasks,
        branch_id=branch_id,
    )

    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)
    return new_employee

def delete_employee(db: Session, employee_id: int):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        return None

    # If the employee is linked to a user account, delete it as well.
    if employee.user:
        db.delete(employee.user)
    else:
        db.delete(employee)
    db.commit()
    return employee