from pydantic import BaseModel
from typing import List, Optional

from .food_category import FoodCategoryOut

class FoodItemImageOut(BaseModel):
    id: int
    image_url: str

    class Config:
        from_attributes = True

class FoodItemCreate(BaseModel):
    name: str
    description: str
    price: float
    available: bool
    category_id: int
    always_available: bool = True
    available_from_time: Optional[str] = None
    available_to_time: Optional[str] = None
    time_wise_prices: Optional[str] = None
    room_service_price: Optional[float] = None
    extra_inventory_items: Optional[str] = None

class FoodItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    available: Optional[bool] = None
    category_id: Optional[int] = None
    always_available: Optional[bool] = None
    available_from_time: Optional[str] = None
    available_to_time: Optional[str] = None
    time_wise_prices: Optional[str] = None
    room_service_price: Optional[float] = None
    extra_inventory_items: Optional[str] = None

class FoodItemOut(BaseModel):
    id: int
    name: str
    description: str
    price: float
    available: bool
    category_id: int
    always_available: bool = True
    available_from_time: Optional[str] = None
    available_to_time: Optional[str] = None
    time_wise_prices: Optional[str] = None
    room_service_price: Optional[float] = None
    extra_inventory_items: Optional[str] = None
    images: List[FoodItemImageOut] = []
    category: Optional[FoodCategoryOut] = None

    class Config:
        from_attributes = True
