from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class NotificationType(str, enum.Enum):
    SERVICE = "service"
    BOOKING = "booking"
    PACKAGE = "package"
    INVENTORY = "inventory"
    EXPENSE = "expense"
    FOOD_ORDER = "food_order"
    SUCCESS = "success"
    ERROR = "error"
    INFO = "info"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(SQLEnum(NotificationType), nullable=False, default=NotificationType.INFO)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Optional metadata for linking to specific entities
    entity_type = Column(String(50), nullable=True)  # e.g., "booking", "service", "expense"
    entity_id = Column(Integer, nullable=True)  # ID of the related entity
    recipient_id = Column(Integer, nullable=True) # ID of the user who receives this notification (NULL for global)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    
    branch = relationship("Branch")


