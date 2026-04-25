"""
Recipe model for linking food items to inventory items
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import timezone, datetime
from app.database import Base


class Recipe(Base):
    __tablename__ = "recipes"
    
    id = Column(Integer, primary_key=True, index=True)
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    name = Column(String, nullable=False)  # Recipe name (can be same as food item or custom)
    description = Column(Text, nullable=True)  # Recipe description/instructions
    servings = Column(Integer, default=1)  # Number of servings this recipe makes
    prep_time_minutes = Column(Integer, nullable=True)  # Preparation time in minutes
    cook_time_minutes = Column(Integer, nullable=True)  # Cooking time in minutes
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    food_item = relationship("FoodItem", back_populates="recipes")
    ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")
    branch = relationship("Branch")

    __table_args__ = (UniqueConstraint('name', 'branch_id', name='uix_recipe_name_branch'),)


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    
    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    quantity = Column(Float, nullable=False)  # Quantity needed
    unit = Column(String, nullable=False)  # Unit of measurement (kg, liter, pcs, etc.)
    notes = Column(String, nullable=True)  # Optional notes (e.g., "chopped", "diced")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    recipe = relationship("Recipe", back_populates="ingredients")
    inventory_item = relationship("InventoryItem")



