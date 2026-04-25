from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Date, Enum, func, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from datetime import timezone, datetime
from app.database import Base
import enum


class CheckoutRequest(Base):
    """Pre-checkout request for inventory verification"""
    __tablename__ = "checkout_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    package_booking_id = Column(Integer, ForeignKey("package_bookings.id"), nullable=True)
    room_number = Column(String, nullable=False)
    guest_name = Column(String, nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    
    branch = relationship("Branch")

    
    # Request status
    status = Column(String, default="pending")  # pending, in_progress, inventory_checked, completed, cancelled
    requested_by = Column(String, nullable=True)  # User who requested
    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Employee assignment
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=True)
    
    # Inventory check status
    inventory_checked = Column(Boolean, default=False)
    inventory_checked_by = Column(String, nullable=True)
    inventory_checked_at = Column(DateTime, nullable=True)

    inventory_notes = Column(Text, nullable=True)
    inventory_data = Column(JSON, nullable=True)  # Stores verified inventory items (used/missing)
    
    # Completion
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Link to checkout after approval
    checkout_id = Column(Integer, ForeignKey("checkouts.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    employee = relationship("Employee", foreign_keys=[employee_id], back_populates="checkout_requests")
    booking = relationship("Booking", foreign_keys=[booking_id])
    package_booking = relationship("PackageBooking", foreign_keys=[package_booking_id])


class CheckoutVerification(Base):
    """Pre-checkout verification records"""
    __tablename__ = "checkout_verifications"
    
    id = Column(Integer, primary_key=True, index=True)
    checkout_id = Column(Integer, ForeignKey("checkouts.id"), nullable=False)
    checkout_request_id = Column(Integer, ForeignKey("checkout_requests.id"), nullable=True)  # Link to original request
    room_number = Column(String, nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    
    branch = relationship("Branch")

    
    # Room Inspection
    housekeeping_status = Column(String, default="pending")  # pending, approved, issues_found
    housekeeping_notes = Column(Text, nullable=True)
    housekeeping_approved_by = Column(String, nullable=True)
    housekeeping_approved_at = Column(DateTime, nullable=True)
    
    # Consumables Audit
    consumables_audit_data = Column(JSON, nullable=True)  # {item_id: {actual: int, limit: int, charge: float}}
    consumables_total_charge = Column(Float, default=0.0)
    
    # Asset Damage Check
    asset_damages = Column(JSON, nullable=True)  # [{item_name: str, replacement_cost: float, notes: str}]
    asset_damage_total = Column(Float, default=0.0)
    
    # Key Card Return
    key_card_returned = Column(Boolean, default=False)
    key_card_fee = Column(Float, default=0.0)  # Charge if not returned
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    checkout = relationship("Checkout", back_populates="verifications")


class CheckoutPayment(Base):
    """Split payment records for checkout"""
    __tablename__ = "checkout_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    checkout_id = Column(Integer, ForeignKey("checkouts.id"), nullable=False)
    payment_method = Column(String, nullable=False)  # cash, card, upi, bank_transfer
    amount = Column(Float, nullable=False)
    transaction_id = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    
    branch = relationship("Branch")

    
    checkout = relationship("Checkout", back_populates="payments")


class Checkout(Base):
    __tablename__ = "checkouts"
    id = Column(Integer, primary_key=True, index=True)

    room_total = Column(Float, default=0.0)
    food_total = Column(Float, default=0.0)
    service_total = Column(Float, default=0.0)
    package_total = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    grand_total = Column(Float, default=0.0)
    guest_name = Column(String, default="")
    room_number = Column(String, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    checkout_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    payment_method = Column(String, default="")
    
    # Enhanced fields
    late_checkout_fee = Column(Float, default=0.0)
    consumables_charges = Column(Float, default=0.0)  # Total from consumables audit
    inventory_charges = Column(Float, default=0.0)    # Total from rentals
    asset_damage_charges = Column(Float, default=0.0)  # Total from asset damages
    key_card_fee = Column(Float, default=0.0)
    advance_deposit = Column(Float, default=0.0)  # Advance paid during booking
    tips_gratuity = Column(Float, default=0.0)

    # Detailed Bill Breakdown
    bill_details = Column(JSON, nullable=True)  # Snapshot of all line items (Room, Food, Service, Inventory, Assets)
    
    # B2B/GSTIN
    guest_gstin = Column(String, nullable=True)  # For B2B invoices
    is_b2b = Column(Boolean, default=False)
    invoice_number = Column(String, nullable=True, unique=True, index=True)
    
    # Documents
    invoice_pdf_path = Column(String, nullable=True)
    gate_pass_path = Column(String, nullable=True)
    feedback_sent = Column(Boolean, default=False)
    
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True, unique=True)
    package_booking_id = Column(Integer, ForeignKey("package_bookings.id"), nullable=True, unique=True)
    payment_status = Column(String) 
    notes = Column(Text, nullable=True) # General notes for the checkout record
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    
    branch = relationship("Branch")


    booking = relationship("Booking", back_populates="checkout", uselist=False)
    package_booking = relationship("PackageBooking", back_populates="checkout", uselist=False)
    verifications = relationship("CheckoutVerification", back_populates="checkout", cascade="all, delete-orphan")
    payments = relationship("CheckoutPayment", back_populates="checkout", cascade="all, delete-orphan")