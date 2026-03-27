# models/food_category.py
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class FoodCategory(Base):
    __tablename__ = "food_categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    image = Column(String, nullable=True)  # Path to category image
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True, server_default="1")
    
    branch = relationship("Branch")

    __table_args__ = (UniqueConstraint('name', 'branch_id', name='uix_food_category_name_branch'),)
