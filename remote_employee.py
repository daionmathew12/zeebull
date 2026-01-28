# app/api/employee.py

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.database import SessionLocal
from app.schemas.employee import Employee, LeaveCreate, LeaveOut, EmployeeStatusOverview, SalaryPaymentCreate, SalaryPaymentOut
from app.schemas.user import UserCreate
# ??? Corrected imports to point to the crud modules
from app.curd import employee as crud_employee
from app.curd import user as crud_user
from app.models.employee import Employee as EmployeeModel, Leave as LeaveModel, WorkingLog as WorkingLogModel
from app.models.salary_payment import SalaryPayment
from app.models.settings import SystemSetting
from app.models.user import User
from app.utils.auth import get_current_user, get_db
import os
import shutil
import json
from datetime import date 

router = APIRouter(prefix="/employees", tags=["Employees"])

# get_db is now imported from utils.auth to ensure consistency


# Create upload directory if it doesn't exist
UPLOAD_DIR = "uploads/employees"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("")
def add_employee(
    db: Session = Depends(get_db),
    name: str = Form(...),
    role: str = Form(...),
    salary: float = Form(...),
    join_date: str = Form(...),
    email: str = Form(...),
    phone: str = Form(None),
    password: str = Form(...),
    image: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
):
    image_url = None
    if image and image.filename:
        upload_folder = "uploads"
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, image.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        image_url = file_path.replace("\\", "/")

    if crud_user.get_user_by_email(db, email=email):
        raise HTTPException(status_code=400, detail="Email already registered")

    role_obj = crud_employee.get_role_by_name(db, role_name=role)
    if not role_obj:
        raise HTTPException(status_code=404, detail="Role not found")
        
    user_data = UserCreate(
        email=email,
        password=password,
        name=name,
        phone=phone,
        role_id=role_obj.id,
    )
    
    new_user = crud_user.create_user(db=db, user=user_data)

    try:
        parsed_join_date = date.fromisoformat(join_date)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Invalid date format. Use YYYY-MM-DD."
        )

    return crud_employee.create_employee_with_image(
        db,
        name=name,
        role=role,
        salary=salary,
        join_date=parsed_join_date,
        image_url=image_url,
        user_id=new_user.id,
    )

def _list_employees_impl(db: Session, current_user: User, skip: int = 0, limit: int = 20):
    """Helper function for list_employees with status calculation"""
    if limit > 50:
        limit = 50
    if limit < 1:
        limit = 20
        
    employees = crud_employee.get_employees(db, skip=skip, limit=limit)
    
    # Calculate status logic
    today = date.today()
    
    # 2. Check Leave status (Pre-fetch for efficiency)
    active_leaves = db.query(LeaveModel).filter(
        LeaveModel.status == 'approved',
        LeaveModel.from_date <= today,
        LeaveModel.to_date >= today
    ).all()
    leave_employee_ids = {leave.employee_id for leave in active_leaves}
    
    # 3. Check working status (Pre-fetch for efficiency)
    today_logs = db.query(WorkingLogModel).filter(
        WorkingLogModel.date == today
    ).all()
    
    # Map employee_id to their working status
    working_status_map = {}
    for log in today_logs:
        if log.check_out_time is None:
            working_status_map[log.employee_id] = "on_duty"
        else:
            working_status_map[log.employee_id] = "off_duty"
    
    # Build the response with status
    result = []
    for emp in employees:
        # Determine status
        if emp.id in leave_employee_ids:
            status = "on_leave"
        elif emp.id in working_status_map:
            status = working_status_map[emp.id]
        else:
            status = "off_duty"
        
        # Build response object
        # Build user dict safely
        user_dict = None
        if emp.user:
            user_dict = {
                "id": emp.user.id,
                "email": emp.user.email,
                "name": emp.user.name,
                "phone": emp.user.phone,
                "is_active": emp.user.is_active,
            }
        
        emp_dict = {
            "id": emp.id,
            "name": emp.name,
            "role": emp.role,
            "salary": emp.salary,
            "join_date": str(emp.join_date) if emp.join_date else None,
            "image_url": emp.image_url,
            "user_id": emp.user_id,
            "status": status,
            "user": user_dict
        }
        result.append(emp_dict)
    
    return result

@router.get("")
def list_employees(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 20
):
    return _list_employees_impl(db, current_user, skip, limit)

@router.get("/status-overview", response_model=EmployeeStatusOverview)
def get_employee_status_overview(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Returns lists of employees based on their status today:
    - active_employees: on duty (clocked in)
    - inactive_employees: off duty (not clocked in)
    - on_paid_leave: approved paid leave
    - on_sick_leave: approved sick leave
    - on_unpaid_leave: approved unpaid leave
    """
    today = date.today()
    employees = db.query(EmployeeModel).all()
    
    # Pre-fetch approved leaves for today
    active_leaves = db.query(LeaveModel).filter(
        LeaveModel.status == 'approved',
        LeaveModel.from_date <= today,
        LeaveModel.to_date >= today
    ).all()
    
    # Map employee_id -> leave_type
    leave_map = {l.employee_id: l.leave_type for l in active_leaves}
    
    # Pre-fetch today's active working logs (clocked in, not checked out)
    active_logs = db.query(WorkingLogModel).filter(
        WorkingLogModel.date == today,
        WorkingLogModel.check_out_time.is_(None)
    ).all()
    on_duty_ids = {log.employee_id for log in active_logs}
    
    result = {
        "active_employees": [],
        "inactive_employees": [],
        "on_paid_leave": [],
        "on_sick_leave": [],
        "on_unpaid_leave": []
    }
    
    for emp in employees:
        if emp.id in on_duty_ids:
            result["active_employees"].append(emp)
        elif emp.id in leave_map:
            l_type = leave_map[emp.id]
            if l_type == "Sick":
                result["on_sick_leave"].append(emp)
            elif l_type == "Unpaid":
                result["on_unpaid_leave"].append(emp)
            else:
                # Default to paid for "Paid", "Long", "Wellness", or unknown
                result["on_paid_leave"].append(emp)
        else:
            result["inactive_employees"].append(emp)
            
    return result

@router.get("/me")
@router.get("/me/")
def get_myself(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.employee:
        return current_user.employee
    
    # Self-Healing: Try to find unlinked employee by matching name/email parts
    search_name = current_user.name
    emp = None
    if search_name:
         emp = db.query(EmployeeModel).filter(EmployeeModel.name.ilike(f"%{search_name}%")).first()
    
    if not emp and current_user.email:
         # Try email username part
         username = current_user.email.split('@')[0]
         emp = db.query(EmployeeModel).filter(EmployeeModel.name.ilike(f"%{username}%")).first()
         
    if emp:
        # Link if found (Self-Healing)
        if emp.user_id is None: 
            emp.user_id = current_user.id
            db.commit()
            db.refresh(emp)
        return emp
            
    raise HTTPException(status_code=404, detail="No linked employee profile")

@router.get("/{employee_id}")
def get_employee(employee_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    employee = db.query(EmployeeModel).options(joinedload(EmployeeModel.user)).filter(EmployeeModel.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return {
        "id": employee.id,
        "name": employee.name,
        "role": employee.role,
        "salary": employee.salary,
        "join_date": str(employee.join_date) if employee.join_date else None,
        "image_url": employee.image_url,
        "user_id": employee.user_id,
        "paid_leave_balance": employee.paid_leave_balance,
        "sick_leave_balance": employee.sick_leave_balance,
        "long_leave_balance": employee.long_leave_balance,
        "wellness_leave_balance": employee.wellness_leave_balance,
        "user": {
            "id": employee.user.id,
            "email": employee.user.email,
            "name": employee.user.name,
            "phone": employee.user.phone,
            "is_active": employee.user.is_active,
        } if employee.user else None
    }

@router.put("/{employee_id}")
def update_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    name: str = Form(None),
    role: str = Form(None),
    salary: float = Form(None),
    join_date: str = Form(None),
    email: str = Form(None),
    phone: str = Form(None),
    image: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
):
    employee = db.query(EmployeeModel).options(joinedload(EmployeeModel.user)).filter(EmployeeModel.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if name: 
        employee.name = name
        if employee.user: employee.user.name = name
    
    if role:
        role_obj = crud_employee.get_role_by_name(db, role_name=role)
        if not role_obj:
            raise HTTPException(status_code=404, detail="Role not found")
        employee.role = role
        if employee.user: employee.user.role_id = role_obj.id

    if salary is not None: employee.salary = salary
    
    if join_date:
        try:
            employee.join_date = date.fromisoformat(join_date)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid date format")

    if image and image.filename:
        upload_folder = "uploads"
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, image.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        employee.image_url = file_path.replace("\\", "/")

    if email and employee.user:
        if email != employee.user.email:
            existing = crud_user.get_user_by_email(db, email=email)
            if existing and existing.id != employee.user.id:
                raise HTTPException(status_code=400, detail="Email already used")
            employee.user.email = email
    
    if phone and employee.user:
        employee.user.phone = phone

    db.commit()
    db.refresh(employee)
    
    return {
        "id": employee.id,
        "name": employee.name,
        "role": employee.role,
        "salary": employee.salary,
        "join_date": str(employee.join_date) if employee.join_date else None,
        "image_url": employee.image_url,
        "user_id": employee.user_id,
        "paid_leave_balance": employee.paid_leave_balance,
        "sick_leave_balance": employee.sick_leave_balance,
        "long_leave_balance": employee.long_leave_balance,
        "wellness_leave_balance": employee.wellness_leave_balance,
        "user": {
            "id": employee.user.id,
            "email": employee.user.email,
            "name": employee.user.name,
            "phone": employee.user.phone,
            "is_active": employee.user.is_active,
        } if employee.user else None
    }

@router.delete("/{employee_id}")
def delete_employee(employee_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    deleted_employee = crud_employee.delete_employee(db, employee_id)
    if not deleted_employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Employee deleted successfully", "employee": deleted_employee}

# Leave Management Endpoints

@router.get("/leave-policy")
def get_leave_policy(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    policy = db.query(SystemSetting).filter(SystemSetting.key == "leave_policy").first()
    if not policy:
        return {
            "paid_leave_monthly": 4,
            "paid_leave_yearly": 48,
            "sick_leave_monthly": 1,
            "sick_leave_yearly": 12,
            "long_leave_monthly": 0,
            "long_leave_yearly": 5,
            "wellness_leave_monthly": 0,
            "wellness_leave_yearly": 5,
        }
    return json.loads(policy.value)

@router.post("/leave-policy")
def save_leave_policy(payload: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    policy = db.query(SystemSetting).filter(SystemSetting.key == "leave_policy").first()
    if not policy:
        policy = SystemSetting(key="leave_policy", value=json.dumps(payload))
        db.add(policy)
    else:
        policy.value = json.dumps(payload)
    db.commit()
    return {"message": "Policy updated successfully"}

@router.post("/leave", response_model=LeaveOut)
def apply_leave(leave: LeaveCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud_employee.create_leave(db, leave)

@router.get("/pending-leaves", response_model=list[LeaveOut])
def get_pending_leaves(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(LeaveModel).filter(LeaveModel.status == 'pending').all()

@router.get("/leave/{employee_id}", response_model=list[LeaveOut])
def view_leaves(employee_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user), skip: int = 0, limit: int = 100):
    return crud_employee.get_employee_leaves(db, employee_id, skip=skip, limit=limit)

@router.put("/leave/{leave_id}/status/{status}", response_model=LeaveOut)
def update_leave_status(leave_id: int, status: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud_employee.update_leave_status(db, leave_id, status)

# Salary Payment Endpoints

@router.get("/{employee_id}/salary-payments")
def get_salary_payments(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 12
):
    """Get salary payment history for an employee"""
    payments = db.query(SalaryPayment).filter(
        SalaryPayment.employee_id == employee_id
    ).order_by(
        SalaryPayment.year.desc(),
        SalaryPayment.month_number.desc()
    ).offset(skip).limit(limit).all()
    
    return [{
        "id": p.id,
        "month": p.month,
        "year": p.year,
        "month_number": p.month_number,
        "basic_salary": p.basic_salary,
        "allowances": p.allowances,
        "deductions": p.deductions,
        "net_salary": p.net_salary,
        "payment_date": str(p.payment_date) if p.payment_date else None,
        "payment_method": p.payment_method,
        "payment_status": p.payment_status,
        "notes": p.notes
    } for p in payments]

@router.post("/{employee_id}/salary-payments", response_model=SalaryPaymentOut)
def create_salary_payment(
    employee_id: int,
    payment: SalaryPaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new salary payment record"""
    emp = db.query(EmployeeModel).filter(EmployeeModel.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    net_salary = payment.basic_salary + payment.allowances - payment.deductions
    
    # Check if payment already exists for this month/year
    existing_payment = db.query(SalaryPayment).filter(
        SalaryPayment.employee_id == employee_id,
        SalaryPayment.month_number == payment.month_number,
        SalaryPayment.year == payment.year
    ).first()

    if existing_payment:
        existing_payment.basic_salary = payment.basic_salary
        existing_payment.allowances = payment.allowances
        existing_payment.deductions = payment.deductions
        existing_payment.net_salary = net_salary
        existing_payment.notes = payment.notes
        existing_payment.payment_date = payment.payment_date
        existing_payment.payment_method = payment.payment_method
        
        db.commit()
        db.refresh(existing_payment)
        return existing_payment

    new_payment = SalaryPayment(
        employee_id=employee_id,
        month=payment.month,
        year=payment.year,
        month_number=payment.month_number,
        basic_salary=payment.basic_salary,
        allowances=payment.allowances,
        deductions=payment.deductions,
        net_salary=net_salary,
        payment_date=payment.payment_date,
        payment_method=payment.payment_method,
        payment_status="paid",
        notes=payment.notes
    )
    
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)
    return new_payment
