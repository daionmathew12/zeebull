"""
Employee Inventory Assignment Model
Tracks inventory items assigned to employees for services
"""
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import timezone, datetime
from app.database import Base


class EmployeeInventoryAssignment(Base):
    __tablename__ = "employee_inventory_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    assigned_service_id = Column(Integer, ForeignKey("assigned_services.id"), nullable=True)  # Link to assigned service
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    
    # Quantities
    quantity_assigned = Column(Float, nullable=False, default=0.0)  # Original quantity assigned
    quantity_used = Column(Float, nullable=False, default=0.0)  # Quantity actually used
    quantity_returned = Column(Float, nullable=False, default=0.0)  # Quantity returned to office
    
    # Status tracking
    status = Column(String, default="assigned")  # assigned, in_use, completed, returned
    is_returned = Column(Boolean, default=False)  # Whether items have been returned
    
    # Timestamps
    assigned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    
    branch = relationship("Branch")

    returned_at = Column(DateTime, nullable=True)
    
    # Notes
    notes = Column(String, nullable=True)
    
    # Relationships
    employee = relationship("Employee", back_populates="inventory_assignments")
    assigned_service = relationship("AssignedService")
    item = relationship("InventoryItem")
    
    @property
    def balance_quantity(self):
        """Calculate balance quantity (assigned - used - returned)"""
        return self.quantity_assigned - self.quantity_used - self.quantity_returned
