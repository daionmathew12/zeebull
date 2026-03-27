from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.notification import NotificationType

class NotificationBase(BaseModel):
    type: NotificationType
    title: str
    message: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    recipient_id: Optional[int] = None
    branch_id: Optional[int] = None


class NotificationCreate(NotificationBase):
    pass

class NotificationOut(NotificationBase):
    id: int
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True
