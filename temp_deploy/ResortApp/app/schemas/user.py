from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
import json

# ---------- Role Models ----------
class RoleBase(BaseModel):
    name: str
    permissions: Optional[List[str]] = []

class RoleCreate(RoleBase):
    permissions: Optional[str] = None # Accept as string from frontend

class RoleOut(RoleBase):
    id: int
    name: str
    permissions: Optional[List[str]] = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator('permissions', mode='before')
    @classmethod
    def parse_permissions(cls, v):
        """Convert permissions from JSON string to list"""
        if v is None:
            return []
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        if isinstance(v, list):
            return v
        return []

# ---------- User Models ----------
class UserBase(BaseModel):
    name: str
    email: EmailStr  # Use EmailStr for email validation
    phone: Optional[str] = None
    branch_id: Optional[int] = None


class UserCreate(UserBase):
    password: str
    role_id: int
    is_superadmin: bool = False


class AdminSetupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserOut(UserBase):
    id: int
    role: Optional[RoleOut] = None
    phone: Optional[str]
    is_active: bool
    branch_id: Optional[int]
    is_superadmin: bool

    model_config = ConfigDict(from_attributes=True)
