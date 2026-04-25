from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Table, Boolean
from sqlalchemy.orm import relationship
from datetime import timezone, datetime
from app.database import Base
import enum

class ServiceStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"

# Association table for many-to-many relationship between Service and InventoryItem
service_inventory_item = Table(
    'service_inventory_items',
    Base.metadata,
    Column('service_id', Integer, ForeignKey('services.id'), primary_key=True),
    Column('inventory_item_id', Integer, ForeignKey('inventory_items.id'), primary_key=True),
    Column('quantity', Float, default=1.0, nullable=False),  # Quantity of item needed for this service
    Column('created_at', DateTime, default=lambda: datetime.now(timezone.utc))
)

class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    charges = Column(Float, nullable=False)
    gst_rate = Column(Float, default=0.18)  # GST rate for this service (default 18%)
    is_visible_to_guest = Column(Boolean, default=False, nullable=False)  # Toggle for guest visibility
    average_completion_time = Column(String, nullable=True)  # e.g., "30 minutes", "1 hour"
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    images = relationship("ServiceImage", back_populates="service", cascade="all, delete-orphan")
    inventory_items = relationship(
        "InventoryItem",
        secondary=service_inventory_item,
        back_populates="services"
    )

class AssignedService(Base):
    __tablename__ = "assigned_services"
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"))
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"))
    room_id = Column(Integer, ForeignKey("rooms.id"))
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    package_booking_id = Column(Integer, ForeignKey("package_bookings.id"), nullable=True)
    assigned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(Enum(ServiceStatus), default=ServiceStatus.pending)
    billing_status = Column(String, default="unbilled")
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    
    branch = relationship("Branch")

    last_used_at = Column(DateTime, nullable=True)  # Timestamp when service was last used (marked during checkout)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    override_charges = Column(Float, nullable=True)  # Manual override for service charges (e.g. for damages)

    service = relationship("Service")
    employee = relationship("Employee", back_populates="assigned_services")
    room = relationship("Room")
    booking = relationship("Booking", backref="assigned_services")
    package_booking = relationship("PackageBooking", backref="assigned_services")
    # inventory_assignments relationship is defined in employee_inventory.py via backref


class ServiceImage(Base):
    __tablename__ = "service_images"
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"))
    image_url = Column(String, nullable=False)
    
    # Relationships
    service = relationship("Service", back_populates="images")
