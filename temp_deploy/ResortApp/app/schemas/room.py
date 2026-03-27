from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class RoomBase(BaseModel):
    number: str
    type: Optional[str] = None
    price: Optional[float] = None
    adults: int = 2      # new field
    children: int = 0    # new field
    # Room features/amenities
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
    extra_images: Optional[str] = None

class RoomCreate(RoomBase):
    pass

class RoomOut(RoomBase):
    id: int
    status: str
    housekeeping_status: Optional[str] = "Clean"
    housekeeping_updated_at: Optional[datetime] = None
    last_maintenance_date: Optional[date] = None
    image_url: str | None = None
    extra_images: Optional[str] = None
    current_guest_name: Optional[str] = None

    model_config = {
        "from_attributes": True  # enables from_orm in Pydantic v2
    }
