from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, index=True)  # e.g., "GET /api/public/rooms"
    method = Column(String)              # GET, POST, etc.
    path = Column(String)                # /api/public/rooms
    status_code = Column(Integer)        # 200, 404, etc.
    client_ip = Column(String, nullable=True)
    user_id = Column(Integer, nullable=True) # If authenticated
    details = Column(Text, nullable=True)    # JSON string or text details
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True, index=True)
    
    branch = relationship("Branch")

