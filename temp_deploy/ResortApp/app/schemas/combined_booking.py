from datetime import date
from typing import List, Optional
from pydantic import BaseModel

class FoodOrderItemCreate(BaseModel):
    food_item_id: int
    quantity: int

class ServiceBookingCreate(BaseModel):
    service_id: int

class CombinedBookingRequest(BaseModel):
    guest_name: str
    guest_email: str
    guest_mobile: str
    check_in: date
    check_out: date
    room_id: int  # Made compulsory by removing 'Optional'
    package_id: Optional[int] = None # Remains optional
    food_orders: Optional[List[FoodOrderItemCreate]] = None
    service_bookings: Optional[List[ServiceBookingCreate]] = None
class CombinedBookingResponse(BaseModel):
    main_booking_id: int
    main_booking_type: str
    food_order_id: Optional[int] = None
    service_booking_ids: List[int] = []
