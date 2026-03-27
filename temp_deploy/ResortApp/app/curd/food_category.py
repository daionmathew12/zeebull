from sqlalchemy.orm import Session
from app.models.food_category import FoodCategory
from app.schemas.food_category import FoodCategoryCreate

def create_category(db: Session, category: FoodCategoryCreate, branch_id: int):
    new_cat = FoodCategory(name=category.name, branch_id=branch_id)
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return new_cat

def get_categories(db: Session, skip: int = 0, limit: int = 100, branch_id: int = None):
    query = db.query(FoodCategory)
    if branch_id is not None:
        query = query.filter(FoodCategory.branch_id == branch_id)
    return query.offset(skip).limit(limit).all()

def delete_category(db: Session, cat_id: int, branch_id: int):
    cat = db.query(FoodCategory).filter(FoodCategory.id == cat_id, FoodCategory.branch_id == branch_id).first()
    if cat:
        db.delete(cat)
        db.commit()
    return cat

def update_category(db: Session, cat_id: int, name: str, branch_id: int):
    cat = db.query(FoodCategory).filter(FoodCategory.id == cat_id, FoodCategory.branch_id == branch_id).first()
    if cat:
        cat.name = name
        db.commit()
        db.refresh(cat)
    return cat
