from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.payment import PaymentCreate, PaymentOut, VoucherCreate, VoucherOut
from app.models.user import User
from app.curd import payment as crud
from app.utils.auth import get_current_user

router = APIRouter(prefix="/payments", tags=["Payments & Vouchers"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=PaymentOut)
def create_payment(payment: PaymentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.create_payment(db, payment)

@router.get("", response_model=list[PaymentOut])
def get_payments(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), skip: int = 0, limit: int = 20):
    return crud.get_all_payments(db, skip=skip, limit=limit)

@router.post("/voucher", response_model=VoucherOut)
def create_voucher(voucher: VoucherCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.create_voucher(db, voucher)

@router.get("/voucher/{code}", response_model=VoucherOut)
def get_voucher(code: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    voucher = crud.get_voucher_by_code(db, code)
    if not voucher:
        raise HTTPException(status_code=404, detail="Invalid or expired voucher")
    return voucher
