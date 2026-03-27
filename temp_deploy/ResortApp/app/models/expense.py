from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from app.utils.date_utils import get_ist_now

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    description = Column(String)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"))
    image = Column(String, nullable=True)
    department = Column(String, nullable=True)  # Restaurant, Facility, Hotel, Office, Security, Fire & Safety, Housekeeping
    status = Column(String, default="Pending", nullable=False) # Pending, Approved, Rejected, Paid
    created_at = Column(DateTime, default=get_ist_now)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True, server_default="1")
    
    branch = relationship("Branch")

    
    # RCM (Reverse Charge Mechanism) Fields
    rcm_applicable = Column(Boolean, default=False, nullable=False)  # Is RCM applicable?
    rcm_tax_rate = Column(Float, nullable=True)  # Tax rate for RCM (e.g., 5%, 18%)
    nature_of_supply = Column(String, nullable=True)  # GTA, Legal Services, Import of Service, Security Services
    original_bill_no = Column(String, nullable=True)  # Original bill/receipt number from vendor
    self_invoice_number = Column(String, nullable=True, unique=True, index=True)  # Auto-generated self-invoice (SLF-YYYY-XXX)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True)  # Link to vendor if applicable
    rcm_liability_date = Column(Date, nullable=True)  # Date when RCM liability arises (payment date or 60 days from invoice)
    itc_eligible = Column(Boolean, default=True, nullable=False)  # Is ITC eligible for this RCM transaction?

    employee = relationship("Employee", back_populates="expenses")
    vendor = relationship("Vendor", foreign_keys=[vendor_id])
