from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, time, datetime, timedelta, timezone
from pydantic import BaseModel
import pytz

from calendar import monthrange
from app.utils.auth import get_db, get_current_user
from app.models.employee import Attendance, WorkingLog, Employee, Leave
from app.models.settings import SystemSetting
from app.models.user import User
import json

router = APIRouter(prefix="/attendance", tags=["Attendance"])

# --- Pydantic Schemas ---
class AttendanceRecord(BaseModel):
    id: int
    date: date
    status: str
    class Config: from_attributes = True

class WorkingLogRecord(BaseModel):
    id: int
    date: date
    check_in_time: Optional[time]
    check_out_time: Optional[time]
    location: Optional[str]
    duration_hours: Optional[float] = None
    class Config: from_attributes = True

class AttendanceCreate(BaseModel):
    employee_id: int
    date: date
    status: str
    leave_type: Optional[str] = 'Paid'

class WorkingLogCreate(BaseModel):
    employee_id: int
    date: date
    check_in_time: Optional[time] = None
    check_out_time: Optional[time] = None
    location: Optional[str] = None

class MonthlyReport(BaseModel):
    month: int
    year: int
    total_days: int
    present_days: int
    absent_days: int
    paid_leaves_taken: int
    sick_leaves_taken: int
    unpaid_leaves: int
    total_paid_leaves_year: int
    total_sick_leaves_year: int
    paid_leave_balance: int
    sick_leave_balance: int
    base_salary: float
    deductions: float
    net_salary: float

class ClockInCreate(BaseModel):
    employee_id: int
    location: str

class ClockOutCreate(BaseModel):
    employee_id: int

# --- API Endpoints ---

@router.post("/mark", response_model=AttendanceRecord)
def mark_attendance(record: AttendanceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_record = Attendance(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

@router.post("/log-work", response_model=WorkingLogRecord)
def log_working_hours(log: WorkingLogCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_log = WorkingLog(**log.model_dump())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

@router.post("/clock-in", response_model=WorkingLogRecord)
def clock_in(clock_in_data: ClockInCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        print(f"Clocking in request for {clock_in_data.employee_id}")
        # Use Indian Standard Time (IST) manually without pytz
        # IST is UTC+5:30
        ist = timezone(timedelta(hours=5, minutes=30))
        now = datetime.now(ist)
        
        # Check if there's an open clock-in for this employee today
        # Note: We compare date. now.date() returns local date in that timezone
        open_log = db.query(WorkingLog).filter(
            WorkingLog.employee_id == clock_in_data.employee_id,
            WorkingLog.date == now.date(),
            WorkingLog.check_out_time.is_(None)
        ).first()

        if open_log:
            raise HTTPException(status_code=400, detail="Employee is already clocked in. Please clock out first.")

        new_log = WorkingLog(
            employee_id=clock_in_data.employee_id,
            date=now.date(),
            check_in_time=now.time(),
            location=clock_in_data.location
        )
        db.add(new_log)
        db.commit()
        db.refresh(new_log)
        return new_log
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in clock_in: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clock-out", response_model=WorkingLogRecord)
def clock_out(clock_out_data: ClockOutCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Use Indian Standard Time (IST)
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    
    # Find the last open clock-in for this employee
    log_to_close = db.query(WorkingLog).filter(
        WorkingLog.employee_id == clock_out_data.employee_id, 
        WorkingLog.check_out_time.is_(None)
    ).order_by(WorkingLog.check_in_time.desc()).first()

    if not log_to_close:
        raise HTTPException(status_code=404, detail="No open clock-in found to clock out.")
        
    log_to_close.check_out_time = now.time()
    
    # If clocking out on a different day, update the date to the check-out date
    if log_to_close.date != now.date():
        log_to_close.date = now.date()

    db.commit()
    db.refresh(log_to_close)
    return log_to_close

@router.get("/{employee_id}", response_model=List[AttendanceRecord])
def get_attendance_for_employee(employee_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Attendance).filter(Attendance.employee_id == employee_id).order_by(Attendance.date.desc()).all()

@router.get("/work-logs/{employee_id}", response_model=List[WorkingLogRecord])
def get_work_logs_for_employee(employee_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    work_logs = db.query(WorkingLog).filter(WorkingLog.employee_id == employee_id).order_by(WorkingLog.date.desc(), WorkingLog.check_in_time.desc()).all()
    
    results = []
    for log in work_logs:
        duration_hours = None
        if log.check_in_time and log.check_out_time:
            # Combine date with time to create datetime objects for subtraction
            start_dt = datetime.combine(log.date, log.check_in_time)
            end_dt = datetime.combine(log.date, log.check_out_time)
            if end_dt > start_dt:
                duration = end_dt - start_dt
                duration_hours = duration.total_seconds() / 3600
        
        log_data = WorkingLogRecord.model_validate(log)
        log_data.duration_hours = duration_hours
        results.append(log_data)
        
    return results

@router.get("/monthly-report/{employee_id}", response_model=MonthlyReport)
def get_monthly_report(employee_id: int, year: int, month: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # --- Date and Day Calculations ---
    _, total_days_in_month = monthrange(year, month)
    start_of_month = date(year, month, 1)
    end_of_month = date(year, month, total_days_in_month)

    # Calculate present days based on duration (>= 4 hours)
    working_logs = db.query(WorkingLog).filter(
        WorkingLog.employee_id == employee_id,
        WorkingLog.date >= start_of_month,
        WorkingLog.date <= end_of_month
    ).all()
    
    daily_hours = {}
    for log in working_logs:
        duration = 0
        if log.check_in_time and log.check_out_time:
             # Calculate duration
             start_dt = datetime.combine(log.date, log.check_in_time)
             end_dt = datetime.combine(log.date, log.check_out_time)
             if end_dt > start_dt:
                 duration = (end_dt - start_dt).total_seconds() / 3600
        
        d_str = str(log.date)
        daily_hours[d_str] = daily_hours.get(d_str, 0) + duration
        
    # Count days with at least 4 hours of work as "Present" (Half day or Full day)
    present_days = sum(1 for hours in daily_hours.values() if hours >= 4)

    # --- Leave Calculation for the Month ---
    approved_leaves_month = db.query(Leave).filter(
        Leave.employee_id == employee_id,
        Leave.status == 'approved',
        Leave.from_date <= end_of_month,
        Leave.to_date >= start_of_month
    ).all()

    paid_leaves_taken_month = 0
    sick_leaves_taken_month = 0
    for leave in approved_leaves_month:
        # Calculate overlap with the current month
        overlap_start = max(leave.from_date, start_of_month)
        overlap_end = min(leave.to_date, end_of_month)
        if overlap_end >= overlap_start:
            leave_days_in_month = (overlap_end - overlap_start).days + 1
            if leave.leave_type == 'Paid':
                paid_leaves_taken_month += leave_days_in_month
            elif leave.leave_type == 'Sick':
                sick_leaves_taken_month += leave_days_in_month

    # --- Leave Balance Calculation for the Year ---
    policy_row = db.query(SystemSetting).filter(SystemSetting.key == "leave_policy").first()
    policy = json.loads(policy_row.value) if policy_row else {
        "paid_leave_monthly": 4,
        "paid_leave_yearly": 48,
        "sick_leave_monthly": 1,
        "sick_leave_yearly": 12,
    }

    months_of_service = (datetime.now().year - employee.join_date.year) * 12 + datetime.now().month - employee.join_date.month + 1
    
    # Calculate accrued leaves based on monthly rate, capped by yearly max
    accrued_paid = months_of_service * policy.get("paid_leave_monthly", 4)
    total_paid_leaves_year = min(accrued_paid, policy.get("paid_leave_yearly", 48))
    
    accrued_sick = months_of_service * policy.get("sick_leave_monthly", 1)
    total_sick_leaves_year = min(accrued_sick, policy.get("sick_leave_yearly", 12))

    approved_leaves_year = db.query(Leave).filter(Leave.employee_id == employee_id, Leave.status == 'approved').all()
    paid_leaves_used_year = sum([(l.to_date - l.from_date).days + 1 for l in approved_leaves_year if l.leave_type == 'Paid'])
    sick_leaves_used_year = sum([(l.to_date - l.from_date).days + 1 for l in approved_leaves_year if l.leave_type == 'Sick'])

    # --- Final Report ---
    # Assuming non-working days are not tracked. Absent days are total days minus present and on-leave days.
    # This is a simplification; a real system would exclude weekends/holidays.
    absent_days = total_days_in_month - present_days - paid_leaves_taken_month - sick_leaves_taken_month
    unpaid_leaves = max(0, absent_days)

    # --- Salary Calculation ---
    base_salary = employee.salary or 0.0
    if total_days_in_month > 0:
        per_day_salary = base_salary / total_days_in_month
        deductions = per_day_salary * unpaid_leaves
    else:
        deductions = 0
    net_salary = base_salary - deductions

    return MonthlyReport(
        month=month, year=year, total_days=total_days_in_month, present_days=present_days,
        absent_days=unpaid_leaves, paid_leaves_taken=paid_leaves_taken_month, sick_leaves_taken=sick_leaves_taken_month,
        unpaid_leaves=unpaid_leaves, total_paid_leaves_year=total_paid_leaves_year, total_sick_leaves_year=total_sick_leaves_year,
        paid_leave_balance=total_paid_leaves_year - paid_leaves_used_year,
        sick_leave_balance=total_sick_leaves_year - sick_leaves_used_year,
        base_salary=base_salary, deductions=deductions, net_salary=net_salary
    )