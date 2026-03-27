"""
Pydantic schemas for Recipe management
"""
from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime


class RecipeIngredientCreate(BaseModel):
    inventory_item_id: int
    quantity: float
    unit: str
    notes: Optional[str] = None


class RecipeIngredientOut(BaseModel):
    id: int
    inventory_item_id: int
    inventory_item_name: Optional[str] = None
    inventory_item_code: Optional[str] = None
    quantity: float
    unit: str
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True


class RecipeCreate(BaseModel):
    food_item_id: int
    name: str
    description: Optional[str] = None
    servings: int = 1
    prep_time_minutes: int
    cook_time_minutes: int
    ingredients: List[RecipeIngredientCreate] = []

    @field_validator('prep_time_minutes', 'cook_time_minutes', mode='before')
    @classmethod
    def empty_string_to_none(cls, v):
        if v == "":
            return None
        return v


class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    servings: Optional[int] = None
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    ingredients: Optional[List[RecipeIngredientCreate]] = None

    @field_validator('prep_time_minutes', 'cook_time_minutes', 'servings', mode='before')
    @classmethod
    def empty_string_to_none(cls, v):
        if v == "":
            return None
        return v


class RecipeOut(BaseModel):
    id: int
    food_item_id: int
    food_item_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    servings: int
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    ingredients: List[RecipeIngredientOut] = []
    created_at: datetime
    updated_at: datetime
    total_cost: Optional[float] = None  # Calculated cost based on inventory item prices
    
    class Config:
        from_attributes = True
