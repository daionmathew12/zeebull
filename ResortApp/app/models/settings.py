from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), index=True, nullable=False)
    value = Column(Text, nullable=True)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), default=func.now())
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    
    branch = relationship("app.models.branch.Branch")

    __table_args__ = (UniqueConstraint('key', 'branch_id', name='uix_setting_key_branch'),)
