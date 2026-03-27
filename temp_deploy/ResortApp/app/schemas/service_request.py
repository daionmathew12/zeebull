from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.schemas.foodorder import FoodOrderItemOut

class ServiceRequestCreate(BaseModel):
    food_order_id: Optional[int] = None  # Nullable for cleaning/other non-food requests
    room_id: int
    employee_id: Optional[int] = None
    request_type: str = "delivery"
    description: Optional[str] = None
    image_path: Optional[str] = None

class ServiceRequestUpdate(BaseModel):
    status: Optional[str] = None
    employee_id: Optional[int] = None
    description: Optional[str] = None
    billing_status: Optional[str] = None
    return_location_id: Optional[int] = None
    pickup_location_id: Optional[int] = None

class ServiceRequestOut(BaseModel):
    id: int
    food_order_id: Optional[int] = None
    room_id: int
    employee_id: Optional[int] = None
    request_type: str
    description: Optional[str] = None
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    image_path: Optional[str] = None
    food_order_amount: Optional[float] = None
    food_order_gst: Optional[float] = None
    food_order_total: Optional[float] = None
    food_order_status: Optional[str] = None
    room_number: Optional[str] = None
    employee_name: Optional[str] = None
    food_order_billing_status: Optional[str] = None
    food_items: Optional[List[FoodOrderItemOut]] = None
    pickup_location_id: Optional[int] = None
    refill_data: Optional[str] = None
    service: Optional[dict] = None # Optional nested service details
    
    model_config = ConfigDict(from_attributes=True)

