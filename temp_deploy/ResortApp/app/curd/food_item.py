from app.models.food_item import FoodItem, FoodItemImage
from app.schemas.food_item import FoodItemCreate, FoodItemUpdate
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

def create_food_item(db: Session, item: FoodItemCreate, image_paths: list[str], branch_id: int):
    db_item = FoodItem(**item.model_dump(), branch_id=branch_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    for path in image_paths:
        image = FoodItemImage(image_url=path, item_id=db_item.id)
        db.add(image)

    db.commit()
    db.refresh(db_item)
    return db_item

def get_all_food_items(db: Session, skip: int = 0, limit: int = 100, branch_id: int = None):
    query = db.query(FoodItem)
    if branch_id is not None:
        query = query.filter(FoodItem.branch_id == branch_id)
        
    items = (
        query.options(
            joinedload(FoodItem.images),
            joinedload(FoodItem.category)
        )
        .offset(skip)
        .limit(limit)
        .all()
    )
    return items 

def delete_food_item(db: Session, item_id: int, branch_id: int):
    item = db.query(FoodItem).filter(FoodItem.id == item_id, FoodItem.branch_id == branch_id).first()
    if item:
        db.delete(item)
        db.commit()
        return {"msg": "Deleted"}
    return {"msg": "Not found"}

def update_food_item_availability(db: Session, item_id: int, available: bool, branch_id: int):
    item = db.query(FoodItem).filter(FoodItem.id == item_id, FoodItem.branch_id == branch_id).first()
    if item:
        item.available = available
        db.commit()
        return {"msg": "Availability updated"}
    return {"msg": "Item not found"}

def update_food_item(db: Session, item_id: int, item_update: FoodItemUpdate, image_paths: list[str] = None, branch_id: int = None):
    query = db.query(FoodItem).filter(FoodItem.id == item_id)
    if branch_id is not None:
        query = query.filter(FoodItem.branch_id == branch_id)
        
    item = query.first()
    if not item:
        return None
    
    # Update fields if provided
    update_data = item_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
    
    # Update images if provided
    if image_paths is not None:
        # Delete existing images
        db.query(FoodItemImage).filter(FoodItemImage.item_id == item_id).delete()
        # Add new images
        for path in image_paths:
            image = FoodItemImage(image_url=path, item_id=item.id)
            db.add(image)
    
    db.commit()
    db.refresh(item)
    return item
