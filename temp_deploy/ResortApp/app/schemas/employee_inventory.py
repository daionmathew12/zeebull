"""
Schemas for Employee Inventory Assignment
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class EmployeeInventoryAssignmentBase(BaseModel):
    employee_id: int
    assigned_service_id: Optional[int] = None
    item_id: int
    quantity_assigned: float
    quantity_used: float = 0.0
    quantity_returned: float = 0.0
    status: str = "assigned"
    notes: Optional[str] = None


class EmployeeInventoryAssignmentOut(EmployeeInventoryAssignmentBase):
    id: int
    is_returned: bool
    assigned_at: datetime
    returned_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ReturnInventoryRequest(BaseModel):
    """Request to return inventory items"""
    assignment_id: int
    quantity_returned: float
    notes: Optional[str] = None


