from sqlalchemy.orm import Session
from app.models.payment import Payment, Voucher
from app.schemas.payment import PaymentCreate, VoucherCreate
from datetime import datetime

def create_payment(db: Session, payment: PaymentCreate):
    new_payment = Payment(**payment.dict())
    db.add(new_payment)
    db.commit()
    db.refresh(new_payment)
    return new_payment

def get_all_payments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Payment).offset(skip).limit(limit).all()

def create_voucher(db: Session, voucher: VoucherCreate):
    new_voucher = Voucher(**voucher.dict())
    db.add(new_voucher)
    db.commit()
    db.refresh(new_voucher)
    return new_voucher

def get_voucher_by_code(db: Session, code: str):
    voucher = db.query(Voucher).filter(Voucher.code == code).first()
    if voucher and voucher.expiry_date > datetime.utcnow():
        return voucher
    return None
