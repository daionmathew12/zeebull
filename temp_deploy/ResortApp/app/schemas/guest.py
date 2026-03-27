from pydantic import BaseModel
from typing import Optional

class GuestSuggestion(BaseModel):
    guest_name: str
    guest_email: str
    guest_mobile: Optional[str] = None

    class Config:
        from_attributes = True
