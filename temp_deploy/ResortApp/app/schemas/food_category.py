# schemas/food_category.py
from pydantic import BaseModel

class FoodCategoryBase(BaseModel):
    name: str

class FoodCategoryCreate(FoodCategoryBase):
    pass

class FoodCategoryOut(FoodCategoryBase):
    id: int
    image: str | None

    class Config:
        from_attributes = True
