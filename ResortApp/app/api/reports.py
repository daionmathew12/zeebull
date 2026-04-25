from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date, datetime
from app.utils.date_utils import get_ist_now, get_ist_today
from pydantic import BaseModel

from app.utils.auth import get_db, get_current_user
from app.models.booking import Booking
from app.models.user import User
from app.models.expense import Expense
from app.models.service import AssignedService
from app.models.foodorder import FoodOrder
from app.models.Package import PackageBooking
from app.models.employee import Employee, WorkingLog

router = APIRouter(prefix="/reports", tags=["Reports"])

# --- Pydantic Schemas for Report Outputs ---

class CheckinByEmployeeOut(BaseModel):
    employee_name: str
    checkin_count: int

class ExpenseOut(BaseModel):
    id: int
    category: str
    description: Optional[str]
    amount: float
    date: date
    class Config: from_attributes = True

class ServiceChargeOut(BaseModel):
    id: int
    room_number: Optional[str]
    service_name: Optional[str]
    amount: Optional[float]
    employee_name: Optional[str]
    status: str
    created_at: date
    class Config: from_attributes = True

class FoodOrderOut(BaseModel):
    id: int
    room_number: Optional[str]
    item_count: int
    amount: float
    employee_name: Optional[str]
    status: str
    created_at: date
    class Config: from_attributes = True

class ActivityItem(BaseModel):
    activity_date: datetime
    type: str # e.g. "Booking", "Service", "Attendance", "Food Order"
    description: str
    amount: Optional[float] = None

class UserHistoryOut(BaseModel):
    user_name: str
    activities: List[ActivityItem]

class GlobalActivityItem(ActivityItem):
    user_name: str

# --- Report Endpoints ---

@router.get("/global-activity", response_model=List[GlobalActivityItem])
def get_global_activity_report(
    from_date: Optional[date] = None, 
    to_date: Optional[date] = None, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    """
    Generates a consolidated report of activities across ALL employees.
    """
    activities = []

    # 1. Bookings
    booking_query = db.query(Booking, User).join(User, Booking.user_id == User.id)
    if from_date: booking_query = booking_query.filter(Booking.created_at >= from_date)
    if to_date: booking_query = booking_query.filter(Booking.created_at <= to_date)
    
    for b, u in booking_query.all():
        activities.append(GlobalActivityItem(
            activity_date=b.created_at or get_ist_now(),
            type="Booking",
            description=f"Created booking for {b.guest_name or 'Unknown'} (Room count: {len(b.rooms)})",
            amount=b.total_amount,
            user_name=u.name
        ))

    # 2. Services Assigned (Completed)
    srv_query = db.query(AssignedService, Employee, User).join(Employee, AssignedService.employee_id == Employee.id).join(User, Employee.user_id == User.id)
    if from_date: srv_query = srv_query.filter(AssignedService.assigned_at >= from_date) # Approx
    
    all_services = srv_query.all()
    for s, emp, u in all_services:
        s_status = s.status.value if hasattr(s.status, 'value') else str(s.status)
        if s_status.lower() != "completed":
            continue
            
        act_date = s.last_used_at or s.assigned_at or get_ist_now()
        if from_date and act_date.date() < from_date: continue
        if to_date and act_date.date() > to_date: continue

        service_name = s.service.name if s.service else "Unknown Service"
        room_num = s.room.number if s.room else "Unknown Room"
        activities.append(GlobalActivityItem(
            activity_date=act_date,
            type="Service",
            description=f"Completed service: {service_name} in Room {room_num}",
            amount=None,
            user_name=u.name
        ))

    # 3. Expenses
    exp_query = db.query(Expense, Employee, User).join(Employee, Expense.employee_id == Employee.id).join(User, Employee.user_id == User.id)
    if from_date: exp_query = exp_query.filter(Expense.date >= from_date)
    if to_date: exp_query = exp_query.filter(Expense.date <= to_date)
    
    for e, emp, u in exp_query.all():
        activities.append(GlobalActivityItem(
            activity_date=datetime.combine(e.date, datetime.min.time()),
            type="Expense",
            description=f"Reported expense: {e.category} - {e.description or ''}",
            amount=e.amount,
            user_name=u.name
        ))

    # 4. Working Logs
    wl_query = db.query(WorkingLog, Employee, User).join(Employee, WorkingLog.employee_id == Employee.id).join(User, Employee.user_id == User.id)
    if from_date: wl_query = wl_query.filter(WorkingLog.date >= from_date)
    if to_date: wl_query = wl_query.filter(WorkingLog.date <= to_date)

    for w, emp, u in wl_query.all():
        check_in = w.check_in_time.strftime("%H:%M") if w.check_in_time else "?"
        check_out = w.check_out_time.strftime("%H:%M") if w.check_out_time else "?"
        activities.append(GlobalActivityItem(
            activity_date=datetime.combine(w.date, w.check_in_time) if w.check_in_time else datetime.combine(w.date, datetime.min.time()),
            type="Attendance",
            description=f"Work Log: {check_in} - {check_out} ({w.location or 'Office'})",
            amount=None,
            user_name=u.name
        ))

    # 5. Food Orders
    fo_query = db.query(FoodOrder, Employee, User).join(Employee, FoodOrder.assigned_employee_id == Employee.id).join(User, Employee.user_id == User.id)
    if from_date: fo_query = fo_query.filter(FoodOrder.created_at >= from_date)
    if to_date: fo_query = fo_query.filter(FoodOrder.created_at <= to_date)

    for f, emp, u in fo_query.all():
        room_num = f.room.number if f.room else "N/A"
        activities.append(GlobalActivityItem(
            activity_date=f.created_at,
            type="Food Order",
            description=f"Served order in Room {room_num} ({len(f.items)} items)",
            amount=f.total_with_gst or f.amount,
            user_name=u.name
        ))

    activities.sort(key=lambda x: x.activity_date, reverse=True)
    return activities

@router.get("/checkin-by-employee", response_model=List[CheckinByEmployeeOut])
def get_checkin_by_employee_report(from_date: Optional[date] = None, to_date: Optional[date] = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Generates a report of how many check-ins each employee has performed.
    Filters by the booking's check-in date.
    """
    query = (
        db.query(
            User.name.label("employee_name"),
            func.count(Booking.id).label("checkin_count"),
        )
        .join(User, Booking.user_id == User.id)
        .filter(Booking.status.in_(["checked-in", "checked_out"]))
    )

    if from_date:
        query = query.filter(Booking.check_in >= from_date)
    if to_date:
        query = query.filter(Booking.check_in <= to_date)

    results = (
        query.group_by(User.name)
        .order_by(func.count(Booking.id).desc())
        .all()
    )
    return results

@router.get("/expenses", response_model=List[ExpenseOut])
def get_expenses_report(from_date: Optional[date] = None, to_date: Optional[date] = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    query = db.query(Expense)
    if from_date: query = query.filter(Expense.date >= from_date)
    if to_date: query = query.filter(Expense.date <= to_date)
    return query.order_by(Expense.date.desc()).all()

@router.get("/room-bookings", response_model=List)
def get_room_bookings_report(from_date: Optional[date] = None, to_date: Optional[date] = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    query = db.query(Booking)
    if from_date: query = query.filter(Booking.check_in >= from_date)
    if to_date: query = query.filter(Booking.check_in <= to_date)
    return query.order_by(Booking.check_in.desc()).all()

@router.get("/user-history", response_model=UserHistoryOut)
def get_user_history_report(
    user_id: int, 
    from_date: Optional[date] = None, 
    to_date: Optional[date] = None, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    employee = db.query(Employee).filter(Employee.user_id == user_id).first()
    
    activities = []

    # 1. Bookings created by User
    booking_query = db.query(Booking).filter(Booking.user_id == user_id)
    if from_date: booking_query = booking_query.filter(Booking.created_at >= from_date)
    if to_date: booking_query = booking_query.filter(Booking.created_at <= to_date) # Assuming timestamp comparison with date works or needs cast
    
    for b in booking_query.all():
        activities.append(ActivityItem(
            activity_date=b.created_at or get_ist_now(),
            type="Booking",
            description=f"Created booking for {b.guest_name or 'Unknown'} (Room count: {len(b.rooms)})",
            amount=b.total_amount
        ))

    if employee:
        # 2. Services Assigned
        # Fetch all services first, then filter. This is safer for Enum/String mismatches and date logic.
        srv_query = db.query(AssignedService).filter(AssignedService.employee_id == employee.id)
        
        all_services = srv_query.all()
        for s in all_services:
            # Check status (handle Enum or string)
            s_status = s.status.value if hasattr(s.status, 'value') else str(s.status)
            if s_status.lower() != "completed":
                continue

            # Determine relevant date: Completion time -> Assignment time -> Now
            act_date = s.last_used_at or s.assigned_at or get_ist_now()
            
            # Apply date filter in Python
            if from_date and act_date.date() < from_date:
                continue
            if to_date and act_date.date() > to_date:
                continue

            service_name = s.service.name if s.service else "Unknown Service"
            room_num = s.room.number if s.room else "Unknown Room"
            # Debugging role detection
            roles_debug = []
            if employee.role: roles_debug.append(str(employee.role).lower())
            if employee.user and employee.user.role: roles_debug.append(str(employee.user.role.name).lower())
            
            activities.append(ActivityItem(
                activity_date=act_date,
                type="Service",
                description=f"Completed service: {service_name} in Room {room_num} [Roles: {roles_debug}]",
                amount=None 
            ))

        # 3. Expenses
        exp_query = db.query(Expense).filter(Expense.employee_id == employee.id)
        if from_date: exp_query = exp_query.filter(Expense.date >= from_date)
        if to_date: exp_query = exp_query.filter(Expense.date <= to_date)
        
        for e in exp_query.all():
            activities.append(ActivityItem(
                activity_date=datetime.combine(e.date, datetime.min.time()),
                type="Expense",
                description=f"Reported expense: {e.category} - {e.description or ''}",
                amount=e.amount
            ))

        # 4. Working Logs (Attendance)
        # Using a safer approach with dates for WorkingLog which stores date not datetime
        wl_query = db.query(WorkingLog).filter(WorkingLog.employee_id == employee.id)
        if from_date: wl_query = wl_query.filter(WorkingLog.date >= from_date)
        if to_date: wl_query = wl_query.filter(WorkingLog.date <= to_date)

        for w in wl_query.all():
            check_in = w.check_in_time.strftime("%H:%M") if w.check_in_time else "?"
            check_out = w.check_out_time.strftime("%H:%M") if w.check_out_time else "?"
            activities.append(ActivityItem(
                activity_date=datetime.combine(w.date, w.check_in_time) if w.check_in_time else datetime.combine(w.date, datetime.min.time()),
                type="Attendance",
                description=f"Work Log: {check_in} - {check_out} ({w.location or 'Office'})",
                amount=None
            ))

        # 5. Food Orders
        # 5. Food Orders
        # Logic: If user is kitchen staff, show ALL food orders (since they prepare them).
        # Otherwise, show only orders assigned to the employee (e.g. waiter delivery).
        
        is_kitchen_staff = False
        roles_to_check = []
        if employee.role:
            roles_to_check.append(str(employee.role).lower())
        if employee.user and employee.user.role and employee.user.role.name:
            roles_to_check.append(str(employee.user.role.name).lower())
            
        for r in roles_to_check:
            if "kitchen" in r or "chef" in r or "cook" in r:
                is_kitchen_staff = True
                break
        
        if is_kitchen_staff:
             fo_query = db.query(FoodOrder) # Kitchen sees all
        else:
             fo_query = db.query(FoodOrder).filter(FoodOrder.assigned_employee_id == employee.id)
             
        if from_date: fo_query = fo_query.filter(FoodOrder.created_at >= from_date)
        if to_date: fo_query = fo_query.filter(FoodOrder.created_at <= to_date)

        for f in fo_query.all():
            room_num = f.room.number if f.room else "N/A"
            
            delivery_person = f.employee.name if f.employee else "Unassigned"
            desc = f"Served order in Room {room_num} ({len(f.items)} items)"
            if is_kitchen_staff:
                desc = f"Kitchen Order: Room {room_num} ({len(f.items)} items) - {f.status} | Prep: Kitchen | Del: {delivery_person}"
            
            activities.append(ActivityItem(
                activity_date=f.created_at,
                type="Food Order",
                description=desc,
                amount=f.total_with_gst or f.amount
            ))

    activities.sort(key=lambda x: x.activity_date, reverse=True)

    return UserHistoryOut(user_name=user.name, activities=activities)


# NOTE: Stubs for other report endpoints. You would implement these similarly.
@router.get("/service-charges", response_model=List)
def get_service_charges_report(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)): return []
@router.get("/food-orders", response_model=List)
def get_food_orders_report(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)): return []
@router.get("/package-bookings", response_model=List)
def get_package_bookings_report(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)): return []
@router.get("/employees", response_model=List)
def get_employees_report(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)): return []