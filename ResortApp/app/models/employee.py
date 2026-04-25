from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime, Time
from sqlalchemy.orm import relationship, declarative_base
from app.database import Base # Assuming you have a Base instance

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    role = Column(String)
    salary = Column(Float)
    join_date = Column(Date)
    image_url = Column(String, nullable=True) # ✅ Changed 'image' to 'image_url' for clarity
    daily_tasks = Column(String, nullable=True) # JSON or Text representing daily task list

    # Leave balances (total allocated per year)
    paid_leave_balance = Column(Integer, default=12)
    sick_leave_balance = Column(Integer, default=12)
    long_leave_balance = Column(Integer, default=5)
    wellness_leave_balance = Column(Integer, default=5)
    
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    
    branch = relationship("Branch")

    
    # Relationships with cascade delete
    user = relationship("User", back_populates="employee")
    
    leaves = relationship("Leave", back_populates="employee", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="employee", cascade="all, delete-orphan")
    attendances = relationship("Attendance", back_populates="employee", cascade="all, delete-orphan")
    working_logs = relationship("WorkingLog", back_populates="employee", cascade="all, delete-orphan")
    salary_payments = relationship("SalaryPayment", back_populates="employee", cascade="all, delete-orphan")
    
    # Newly added for full cleanup
    assigned_services = relationship("AssignedService", back_populates="employee", cascade="all, delete-orphan")
    checkout_requests = relationship("CheckoutRequest", back_populates="employee", cascade="all, delete-orphan")
    inventory_assignments = relationship("EmployeeInventoryAssignment", back_populates="employee", cascade="all, delete-orphan")
    
    # Food Order relationships (No cascade delete, just set to NULL on delete)
    assigned_food_orders = relationship("FoodOrder", foreign_keys="[FoodOrder.assigned_employee_id]", back_populates="employee")
    created_food_orders = relationship("FoodOrder", foreign_keys="[FoodOrder.created_by_id]", back_populates="creator")
    prepared_food_orders = relationship("FoodOrder", foreign_keys="[FoodOrder.prepared_by_id]", back_populates="chef")
    
    # Service Request relationship
    service_requests = relationship("ServiceRequest", back_populates="employee")

class Leave(Base):
    __tablename__ = "leaves"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"))
    from_date = Column(Date)
    to_date = Column(Date)
    reason = Column(String)
    leave_type = Column(String, default="Paid") # Leave type: 'Paid', 'Sick', 'Long', 'Wellness'
    status = Column(String, default="pending")
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    
    branch = relationship("Branch")


    employee = relationship("Employee", back_populates="leaves")

class Attendance(Base):
    __tablename__ = "attendances"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String, nullable=False) # e.g., 'Present', 'Absent', 'Leave'
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    
    branch = relationship("Branch")

    
    employee = relationship("Employee", back_populates="attendances")

class WorkingLog(Base):
    __tablename__ = "working_logs"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    check_in_time = Column(Time)
    check_out_time = Column(Time)
    location = Column(String, nullable=True) # e.g., 'Office', 'Remote'
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    completed_tasks = Column(String, nullable=True) # newly added JSON array string for tracked task completion
    is_tasks_approved = Column(Integer, default=0) # 0: Pending, 1: Approved, 2: Rejected (using Integer for more states if needed)
    tasks_approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    tasks_approved_at = Column(DateTime, nullable=True)
    
    clock_in_image = Column(String, nullable=True) # Selfie at clock in
    clock_out_image = Column(String, nullable=True) # Selfie at clock out
    
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    
    branch = relationship("Branch")

    
    employee = relationship("Employee", back_populates="working_logs")