from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

class BookingReportOut(BaseModel):
    id: int
    room_id: int
    guest_email: Optional[str]
    guest_mobile: Optional[str]
    check_in: date
    check_out: date
    guest_name: str
    user_id: int
    status: str

    class Config:
        from_attributes = True

class ServiceChargeReportOut(BaseModel):
    id: int
    room_number: Optional[str]
    employee_name: Optional[str]
    amount: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class FoodOrderReportOut(BaseModel):
    id: int
    room_number: Optional[str]
    employee_name: Optional[str]
    amount: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
class RoomChargeReportOut(BaseModel):
    room_number: str
    total_charges: float

    class Config:
        from_attributes = True  #
