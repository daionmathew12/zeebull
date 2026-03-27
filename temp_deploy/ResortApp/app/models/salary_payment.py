from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class SalaryPayment(Base):
    """Employee salary payment records"""
    __tablename__ = "salary_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    
    # Payment details
    month = Column(String, nullable=False)  # e.g., "January 2026"
    year = Column(Integer, nullable=False)
    month_number = Column(Integer, nullable=False)  # 1-12
    
    # Salary breakdown
    basic_salary = Column(Float, nullable=False)
    allowances = Column(Float, default=0.0)
    deductions = Column(Float, default=0.0)
    net_salary = Column(Float, nullable=False)
    
    # Payment info
    payment_date = Column(Date, nullable=True)
    payment_method = Column(String, nullable=True)  # cash, bank_transfer, cheque
    payment_status = Column(String, default="pending")  # pending, paid
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(String, nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True, server_default="1")
    
    branch = relationship("Branch")

    
    # Relationships
    employee = relationship("Employee", back_populates="salary_payments")
