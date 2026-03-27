from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class ServiceInventoryItemBase(BaseModel):
    inventory_item_id: int
    quantity: float = 1.0

class ServiceBase(BaseModel):
    name: str
    description: Optional[str] = None
    charges: float
    is_visible_to_guest: bool = False  # Toggle for guest visibility
    average_completion_time: Optional[str] = None # e.g., "30 minutes"

class ServiceCreate(ServiceBase):
    inventory_items: Optional[List[ServiceInventoryItemBase]] = []  # List of inventory items with quantities


class ServiceImageOut(BaseModel):
    id: int
    image_url: str

    class Config:
        from_attributes = True


class ServiceInventoryItemOut(BaseModel):
    id: int
    name: str
    item_code: Optional[str] = None
    unit: str
    quantity: float  # Quantity from association table
    unit_price: Optional[float] = 0.0
    selling_price: Optional[float] = None
    
    class Config:
        from_attributes = True

class ServiceOut(ServiceBase):
    id: int
    created_at: datetime
    images: List[ServiceImageOut] = []
    inventory_items: List[ServiceInventoryItemOut] = []  # Include inventory items
    is_visible_to_guest: bool  # Include visibility flag

    class Config:
        from_attributes = True

class ServiceVisibilityUpdate(BaseModel):
    is_visible_to_guest: bool

# For employee and room resolution
class EmployeeOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class RoomOut(BaseModel):
    id: int
    number: str

    class Config:
        from_attributes = True

class ServiceStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"

class AssignedServiceBase(BaseModel):
    service_id: int
    employee_id: int
    room_id: int

class AssignedServiceCreate(AssignedServiceBase):
    override_charges: Optional[float] = None
    billing_status: Optional[str] = "unbilled"  # Explicitly track billing status
    extra_inventory_items: Optional[List[ServiceInventoryItemBase]] = []  # Additional items beyond service template
    inventory_source_selections: Optional[List["InventorySourceSelection"]] = []  # Explicit source for items
    booking_id: Optional[int] = None
    package_booking_id: Optional[int] = None

class InventorySourceSelection(BaseModel):
    item_id: int
    location_id: int

class InventoryReturnItem(BaseModel):
    assignment_id: Optional[int] = None
    inventory_item_id: Optional[int] = None
    quantity_returned: float
    quantity_used: Optional[float] = 0.0  # Allow updating used quantity
    notes: Optional[str] = None
    return_location_id: Optional[int] = None  # Location to return item to

class AssignedServiceUpdate(BaseModel):
    status: Optional[ServiceStatus] = None
    employee_id: Optional[int] = None  # Allow employee reassignment
    inventory_returns: Optional[List[InventoryReturnItem]] = None  # Optional inventory items to return when completing
    return_location_id: Optional[int] = None  # Location to return items to
    billing_status: Optional[str] = None  # Allow updating billing status

class AssignedServiceOut(BaseModel):
    id: int
    service_id: int  # Add for filtering
    employee_id: int  # Add for filtering
    room_id: int  # Add for filtering
    booking_id: Optional[int] = None
    package_booking_id: Optional[int] = None
    service: ServiceOut
    employee: EmployeeOut
    room: RoomOut
    assigned_at: datetime
    status: ServiceStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None  # Timestamp when service was last used (during checkout)
    override_charges: Optional[float] = None
    inventory_items_used: Optional[List[ServiceInventoryItemOut]] = []  # Actual items used (template + extra)
    debug_items: Optional[List[dict]] = None # Debug field to trace data issues

    class Config:
        from_attributes = True

