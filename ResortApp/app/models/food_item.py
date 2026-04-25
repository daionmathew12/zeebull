from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from app.database import Base
from sqlalchemy import UniqueConstraint


class FoodItem(Base):
    __tablename__ = "food_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    price = Column(Float)
    available = Column(Boolean, default=True)
    category_id = Column(Integer, ForeignKey("food_categories.id"))
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    
    branch = relationship("Branch")

    # New fields for time-based details
    available_from_time = Column(String, nullable=True)
    available_to_time = Column(String, nullable=True)
    always_available = Column(Boolean, default=True)
    time_wise_prices = Column(String, nullable=True) # Store as JSON string 
    room_service_price = Column(Float, nullable=True)
    extra_inventory_items = Column(String, nullable=True) # Store as JSON string

    images = relationship("FoodItemImage", back_populates="food_item", cascade="all, delete-orphan")
    category = relationship("FoodCategory", lazy="joined")
    recipes = relationship("Recipe", back_populates="food_item", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint('name', 'branch_id', name='uix_food_item_name_branch'),)


class FoodItemImage(Base):
    __tablename__ = "food_item_images"

    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String)
    item_id = Column(Integer, ForeignKey("food_items.id"))

    food_item = relationship("FoodItem", back_populates="images")