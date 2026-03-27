from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class BranchBase(BaseModel):
    name: str
    code: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    gst_number: Optional[str] = None
    is_active: bool = True

class BranchCreate(BranchBase):
    pass

class BranchUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    gst_number: Optional[str] = None
    is_active: Optional[bool] = None

class Branch(BranchBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
