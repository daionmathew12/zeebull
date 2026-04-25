from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import timezone, datetime
from app.database import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"))
    amount = Column(Float)
    method = Column(String)  # upi, card, cash
    status = Column(String, default="paid")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    
    branch = relationship("Branch")


    booking = relationship("Booking", back_populates="payments")


class Voucher(Base):
    __tablename__ = "vouchers"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True)
    discount_percent = Column(Float)
    expiry_date = Column(DateTime)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    
    branch = relationship("Branch")

