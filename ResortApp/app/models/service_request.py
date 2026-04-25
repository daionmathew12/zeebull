from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import timezone, datetime
from app.database import Base
from app.models.inventory import Location

class ServiceRequest(Base):
    __tablename__ = "service_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    food_order_id = Column(Integer, ForeignKey("food_orders.id"), nullable=True)  # Nullable for cleaning/other non-food requests
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    request_type = Column(String, default="delivery")  # "delivery" or other types
    description = Column(Text, nullable=True)  # Delivery request details
    status = Column(String, default="pending")  # "pending", "in_progress", "completed", "cancelled"
    billing_status = Column(String, nullable=True)  # "paid", "unpaid" for food orders
    refill_data = Column(Text, nullable=True)  # JSON string for refill items data
    image_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    
    branch = relationship("Branch")

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    pickup_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    
    # Relationships
    food_order = relationship("FoodOrder", foreign_keys=[food_order_id])
    room = relationship("Room", foreign_keys=[room_id])
    employee = relationship("Employee", foreign_keys=[employee_id], back_populates="service_requests")
    pickup_location = relationship("Location", foreign_keys=[pickup_location_id])

