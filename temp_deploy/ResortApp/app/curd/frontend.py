from sqlalchemy.orm import Session
import app.models as models
import app.schemas as schemas

# Generic CRUD
def get_all(db: Session, model, skip: int = 0, limit: int = 100):
    return db.query(model).offset(skip).limit(limit).all()

def get_one(db: Session, model, item_id: int):
    return db.query(model).filter(model.id == item_id).first()

def create(db: Session, model, obj_in):
    db_obj = model(**obj_in.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update(db: Session, model, item_id: int, obj_in):
    db_obj = db.query(model).filter(model.id == item_id).first()
    if not db_obj:
        return None
    for key, value in obj_in.dict(exclude_unset=True).items():
        setattr(db_obj, key, value)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete(db: Session, model, item_id: int):
    db_obj = db.query(model).filter(model.id == item_id).first()
    if not db_obj:
        return None
    db.delete(db_obj)
    db.commit()
    return db_obj
