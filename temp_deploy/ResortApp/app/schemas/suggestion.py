from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class GuestSuggestionOut(BaseModel):
    id: int
    guest_name: str
    contact_info: Optional[str] = None
    suggestion: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
