# app/crud/checkout.py
from sqlalchemy.orm import Session
from app.models.checkout import Checkout
from app.schemas.checkout import CheckoutCreate

def create_checkout(db: Session, data: CheckoutCreate):
    checkout = Checkout(**data.dict())
    db.add(checkout)
    db.commit()
    db.refresh(checkout)
    return checkout

def get_checkout_by_room(db: Session, room_id: int):
    return db.query(Checkout).filter(Checkout.room_id == room_id).all()
