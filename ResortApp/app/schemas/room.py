from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class RoomBase(BaseModel):
    number: str
    room_type_id: Optional[int] = None
    extra_images: Optional[str] = None

class RoomCreate(RoomBase):
    pass

class RoomOut(RoomBase):
    id: int
    branch_id: Optional[int] = None
    status: str
    housekeeping_status: Optional[str] = "Clean"
    housekeeping_updated_at: Optional[datetime] = None
    last_maintenance_date: Optional[date] = None
    image_url: str | None = None
    extra_images: Optional[str] = None
    current_guest_name: Optional[str] = None
    inventory_location_id: Optional[int] = None
    
    # Linked Type Data
    type: Optional[str] = None
    price: Optional[float] = 0.0
    adults_capacity: Optional[int] = 2
    children_capacity: Optional[int] = 0
    room_type_image_url: Optional[str] = None
    room_type_extra_images: Optional[str] = None
    
    # Amenities (from RoomType)
    air_conditioning: bool = False
    wifi: bool = False
    bathroom: bool = False
    living_area: bool = False
    terrace: bool = False
    parking: bool = False
    kitchen: bool = False
    family_room: bool = False
    bbq: bool = False
    garden: bool = False
    dining: bool = False
    breakfast: bool = False
    tv: bool = False
    balcony: bool = False
    mountain_view: bool = False
    ocean_view: bool = False
    private_pool: bool = False
    hot_tub: bool = False
    fireplace: bool = False
    pet_friendly: bool = False
    wheelchair_accessible: bool = False
    safe_box: bool = False
    room_service: bool = False
    laundry_service: bool = False
    gym_access: bool = False
    spa_access: bool = False
    housekeeping: bool = False
    mini_bar: bool = False

    model_config = {
        "from_attributes": True  # enables from_orm in Pydantic v2
    }
