from pydantic import BaseModel, Field, model_validator
from datetime import date, datetime
from typing import List, Optional


class PackageImageOut(BaseModel):
    id: int
    image_url: str

    class Config:
        from_attributes = True


class PackageOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    price: float
    booking_type: Optional[str] = "room_type"  # "whole_property" or "room_type"
    room_types: Optional[str] = None  # Comma-separated list of room types
    images: List[PackageImageOut] = Field(default_factory=list)
    theme: Optional[str] = None
    default_adults: int = 2
    default_children: int = 0
    max_stay_days: Optional[int] = None
    food_included: Optional[str] = None
    food_timing: Optional[str] = None
    complimentary: Optional[str] = None

    class Config:
        from_attributes = True


# New schema to represent the Room model
class RoomOut(BaseModel):
    id: int
    number: str
    type: str

    class Config:
        from_attributes = True


# Updated schema to correctly nest the RoomOut model
class PackageBookingRoomOut(BaseModel):
    id: int
    room_id: int
    room: Optional[RoomOut] = None# ✅ match SQLAlchemy relationship

    class Config:
        from_attributes = True

class PackageBookingBase(BaseModel):
    package_id: int
    guest_name: str
    guest_email: Optional[str] = None
    guest_mobile: Optional[str] = None
    check_in: date
    check_out: date
    adults: int = 2
    children: int = 0
    food_preferences: Optional[str] = None
    special_requests: Optional[str] = None
    class Config:
        from_attributes = True


class PackageBookingCreate(PackageBookingBase):
    room_ids: List[int]
    class Config:
        from_attributes = True


class PackageBookingUpdate(BaseModel):
    status: Optional[str] = None
    adults: Optional[int] = None
    children: Optional[int] = None
    class Config:
        from_attributes = True


class PackageBookingOut(PackageBookingBase):
    id: int
    created_at: Optional[datetime] = None # Added for sorting
    display_id: Optional[str] = None  # Format: PK-000001
    status: str
    total_amount: Optional[float] = 0.0
    rooms: List[PackageBookingRoomOut] = Field(default_factory=list)
    package: Optional[PackageOut]
    
    @model_validator(mode='after')
    def set_display_id(self):
        """Auto-generate display_id if not provided"""
        if not self.display_id:
            self.display_id = f"PK-{str(self.id).zfill(6)}"
        return self

    class Config:
        from_attributes = True
