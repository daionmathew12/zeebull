from pydantic import BaseModel, validator, field_validator, model_validator
from typing import List, Optional
from datetime import date, datetime
from .user import UserOut

# This schema is used for displaying Room details within a Booking
class RoomOut(BaseModel):
    id: int
    number: str
    type: Optional[str] = None
    price: Optional[float] = None
    adults: int
    children: int
    status: str
    image_url: Optional[str] = None

    class Config:
        from_attributes = True

# This schema represents the link between a Booking and a Room
class BookingRoomOut(BaseModel):
    booking_id: int
    room_id: int
    room: RoomOut

    class Config:
        from_attributes = True


# This schema is used when creating a new booking
class BookingCreate(BaseModel):
    room_ids: List[int]
    guest_name: str
    guest_mobile: str
    guest_email: str
    check_in: date
    check_out: date
    adults: int
    children: int

    @validator('check_out')
    def validate_booking_duration(cls, v, values):
        """Ensure minimum booking duration of 1 day"""
        if 'check_in' in values:
            check_in = values['check_in']
            if v <= check_in:
                raise ValueError('Check-out date must be at least 1 day after check-in date')
        return v

# This is the main output schema for displaying bookings
class BookingOut(BaseModel):
    id: int
    display_id: Optional[str] = None  # Format: BK-000001
    guest_name: str
    guest_mobile: Optional[str] = None
    guest_email: Optional[str] = None
    status: str
    check_in: date
    check_out: date
    adults: int
    children: int
    # --- CRITICAL FIX: Add the missing image URL fields ---
    id_card_image_url: Optional[str] = None
    guest_photo_url: Optional[str] = None
    user: Optional[UserOut] = None
    is_package: bool = False
    total_amount: float = 0.0
    advance_deposit: float = 0.0
    source: Optional[str] = "Direct"
    package_name: Optional[str] = None
    
    is_id_verified: bool = False
    digital_signature_url: Optional[str] = None
    special_requests: Optional[str] = None
    preferences: Optional[str] = None
    payments: List[object] = []
    # ----------------------------------------------------
    payments: List[object] = []
    # ----------------------------------------------------
    rooms: List[RoomOut] = []
    created_at: Optional[datetime] = None # Added for sorting
    
    # Detailed arrays
    food_orders: List[object] = []
    service_requests: List[object] = []
    inventory_usage: List[object] = []
    
    @model_validator(mode='after')
    def set_display_id(self):
        """Auto-generate display_id if not provided"""
        if not self.display_id:
            self.display_id = f"BK-{str(self.id).zfill(6)}"
        return self

    class Config:
        from_attributes = True
