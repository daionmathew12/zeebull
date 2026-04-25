from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship, backref
from datetime import timezone, datetime
from app.database import Base

class FoodOrder(Base):
    __tablename__ = "food_orders"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"))
    amount = Column(Float)  # Base amount without GST
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True) # Link to booking
    package_booking_id = Column(Integer, ForeignKey("package_bookings.id"), nullable=True) # Link to package booking
    assigned_employee_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    status = Column(String, default="pending")
    billing_status = Column(String, default="unbilled")  # "unbilled", "billed", "paid"
    order_type = Column(String, default="dine_in")  # "dine_in" or "room_service"
    delivery_request = Column(String, nullable=True)  # Delivery request/notes for room service
    payment_method = Column(String, nullable=True)  # "cash", "card", "upi", None (unpaid)
    payment_time = Column(DateTime, nullable=True)  # When payment was made
    gst_amount = Column(Float, nullable=True)  # GST amount (5% of food)
    total_with_gst = Column(Float, nullable=True)  # Total including GST
    is_deleted = Column(Boolean, default=False, nullable=False)  # Soft delete flag
    created_by_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    prepared_by_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc)) # This is UTC, we should handle IST conversion in CRUD if needed or move to IST here.
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    
    branch = relationship("Branch")

    # Actually, let's keep UTC for server and convert in CRUD.

    items = relationship("FoodOrderItem", back_populates="order", cascade="all, delete-orphan")
    employee = relationship("Employee", foreign_keys=[assigned_employee_id], back_populates="assigned_food_orders")
    creator = relationship("Employee", foreign_keys=[created_by_id], back_populates="created_food_orders")
    chef = relationship("Employee", foreign_keys=[prepared_by_id], back_populates="prepared_food_orders")
    room = relationship("Room", back_populates="food_orders")
    booking = relationship("Booking", backref="food_orders")
    package_booking = relationship("PackageBooking", backref="food_orders")

class FoodOrderItem(Base):
    __tablename__ = "food_order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("food_orders.id"))
    food_item_id = Column(Integer, ForeignKey("food_items.id"))
    quantity = Column(Integer)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    
    branch = relationship("Branch")


    order = relationship("FoodOrder", back_populates="items")
    food_item = relationship("FoodItem")

    @property
    def food_item_name(self):
        return self.food_item.name if self.food_item else None

    @property
    def price(self):
        return getattr(self, '_price', 0.0)

    @price.setter
    def price(self, value):
        self._price = value

    @property
    def subtotal(self):
        return getattr(self, '_subtotal', 0.0)

    @subtotal.setter
    def subtotal(self, value):
        self._subtotal = value