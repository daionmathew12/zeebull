from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.database import Base


class GuestSuggestion(Base):
    __tablename__ = "guest_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    guest_name = Column(String(100), nullable=False)
    contact_info = Column(String(100), nullable=True)  # Optional email or phone
    suggestion = Column(Text, nullable=False)
    status = Column(String(50), default="new")  # e.g., 'new', 'reviewed', 'done'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<GuestSuggestion(id={self.id}, guest_name='{self.guest_name}')>"