from pydantic import BaseModel
from typing import Optional, List
from datetime import date

# This schema is used for the API request body when creating a new employee.
# It now includes the required fields: email and password.
class EmployeeCreate(BaseModel):
    name: str
    role: str
    salary: float
    join_date: date
    email: str
    phone: Optional[str] = None
    password: str
    daily_tasks: Optional[str] = None

# This schema is used for the API response body. It defines the data
# that will be returned to the frontend.
class Employee(BaseModel):
    id: int
    name: str
    role: str
    salary: Optional[float] = 0.0
    join_date: Optional[date] = None
    # ✅ It must use 'image_url' to match the database column.
    image_url: Optional[str] = None
    # ✅ It must include 'user_id' to match the database model.
    user_id: Optional[int] = None
    daily_tasks: Optional[str] = None
    
    # Status fields
    current_status: Optional[str] = "Off Duty"
    is_clocked_in: bool = False
    
    class Config:
        # Use from_attributes for Pydantic V2 and above
        from_attributes = True

# Your other schemas for Leave can remain as they are.
class LeaveBase(BaseModel):
    employee_id: Optional[int] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    reason: Optional[str] = None
    leave_type: Optional[str] = "Paid"

class LeaveCreate(LeaveBase):
    pass

class LeaveOut(LeaveBase):
    id: Optional[int] = None
    status: Optional[str] = "pending"
    employee: Optional[Employee] = None # Include full employee details
    
    class Config:
        from_attributes = True

class EmployeeStatusOverview(BaseModel):
    active_employees: List[Employee]
    inactive_employees: List[Employee]
    on_paid_leave: List[Employee]
    on_sick_leave: List[Employee]
    on_unpaid_leave: List[Employee]
    class Config: from_attributes = True

class SalaryPaymentBase(BaseModel):
    month: str
    year: int
    month_number: int
    basic_salary: float
    allowances: float = 0.0
    deductions: float = 0.0
    payment_date: Optional[date] = None
    payment_method: Optional[str] = "cash"
    notes: Optional[str] = None

class SalaryPaymentCreate(SalaryPaymentBase):
    pass

class SalaryPaymentOut(SalaryPaymentBase):
    id: int
    employee_id: int
    net_salary: float
    payment_status: str
    class Config:
        from_attributes = True
