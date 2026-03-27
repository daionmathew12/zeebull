from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class FoodOrderItemCreate(BaseModel):
    food_item_id: int
    quantity: int

class FoodOrderCreate(BaseModel):
    room_id: int
    amount: float
    assigned_employee_id: Optional[int] = None
    prepared_by_id: Optional[int] = None
    items: List[FoodOrderItemCreate]
    status: Optional[str] = "pending"
    billing_status: Optional[str] = "unbilled"
    order_type: Optional[str] = "dine_in"  # "dine_in" or "room_service"
    delivery_request: Optional[str] = None  # Delivery request/notes for room service 
    booking_id: Optional[int] = None
    package_booking_id: Optional[int] = None

class FoodOrderItemOut(BaseModel):
    id: int
    food_item_id: int
    quantity: int
    food_item_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class FoodOrderOut(BaseModel):
    id: int
    room_id: Optional[int] = None
    amount: Optional[float] = 0.0
    status: str
    assigned_employee_id: Optional[int] = None
    prepared_by_id: Optional[int] = None
    billing_status: str 
    payment_method: Optional[str] = None
    order_type: Optional[str] = "dine_in"
    delivery_request: Optional[str] = None
    items: List[FoodOrderItemOut]
    guest_name: Optional[str] = None  # Populated from room's booking
    employee_name: Optional[str] = None  # Populated from employee relationship
    creator_name: Optional[str] = None  # Populated from creator relationship
    chef_name: Optional[str] = None  # Populated from chef relationship
    room_number: Optional[str] = None  # Populated from room relationship
    created_at: Optional[datetime] = None
    booking_id: Optional[int] = None
    package_booking_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class FoodOrderUpdate(BaseModel):
    room_id: Optional[int] = None
    amount: Optional[float] = None
    assigned_employee_id: Optional[int] = None
    created_by_id: Optional[int] = None
    prepared_by_id: Optional[int] = None
    status: Optional[str] = None
    billing_status: Optional[str] = None
    payment_method: Optional[str] = None
    order_type: Optional[str] = None
    delivery_request: Optional[str] = None
    items: Optional[List[FoodOrderItemCreate]] = None
