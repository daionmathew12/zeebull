from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class FoodOrder(Base):
    __tablename__ = "food_orders"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"))
    amount = Column(Float)  # Base amount without GST
    assigned_employee_id = Column(Integer, ForeignKey("employees.id"))
    status = Column(String, default="pending")
    billing_status = Column(String, default="unbilled")  # "unbilled", "billed", "paid"
    order_type = Column(String, default="dine_in")  # "dine_in" or "room_service"
    delivery_request = Column(String, nullable=True)  # Delivery request/notes for room service
    payment_method = Column(String, nullable=True)  # "cash", "card", "upi", None (unpaid)
    payment_time = Column(DateTime, nullable=True)  # When payment was made
    gst_amount = Column(Float, nullable=True)  # GST amount (5% of food)
    total_with_gst = Column(Float, nullable=True)  # Total including GST
    is_deleted = Column(Boolean, default=False, nullable=False)  # Soft delete flag
    created_by_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    prepared_by_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("FoodOrderItem", back_populates="order", cascade="all, delete-orphan")
    employee = relationship("Employee", foreign_keys=[assigned_employee_id])
    creator = relationship("Employee", foreign_keys=[created_by_id])
    chef = relationship("Employee", foreign_keys=[prepared_by_id])
    room = relationship("Room", back_populates="food_orders")

class FoodOrderItem(Base):
    __tablename__ = "food_order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("food_orders.id"))
    food_item_id = Column(Integer, ForeignKey("food_items.id"))
    quantity = Column(Integer)

    order = relationship("FoodOrder", back_populates="items")
    food_item = relationship("FoodItem")

    @property
    def food_item_name(self):
        return self.food_item.name if self.food_item else None