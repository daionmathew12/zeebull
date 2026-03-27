from pydantic import BaseModel
from datetime import datetime

class PaymentBase(BaseModel):
    booking_id: int
    amount: float
    method: str

class PaymentCreate(PaymentBase):
    pass

class PaymentOut(PaymentBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class VoucherBase(BaseModel):
    code: str
    discount_percent: float
    expiry_date: datetime

class VoucherCreate(VoucherBase):
    pass

class VoucherOut(VoucherBase):
    id: int
    class Config:
        from_attributes = True
