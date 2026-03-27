from pydantic import BaseModel
from typing import Optional

class FoodCategoryBase(BaseModel):
    name: str

class FoodCategoryCreate(FoodCategoryBase):
    pass

class FoodCategoryOut(FoodCategoryBase):
    id: int
    branch_id: Optional[int] = None
    image: str | None

    class Config:
        from_attributes = True
