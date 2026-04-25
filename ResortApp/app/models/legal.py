from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey
from app.database import Base
from sqlalchemy.orm import relationship

class LegalDocument(Base):
    __tablename__ = "legal_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    document_type = Column(String, nullable=True)  # e.g., "GST", "License", "Permit"
    file_path = Column(String, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    description = Column(String, nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    
    # Needs import or mapping if relationship is used, but since legal.py doesn't have Branch imported yet:
    # I will stick to just the Column for now or add relationship if I add the import.
    # Actually, relationship works fine with string name in SQLAlchemy if models are discoverable.
    branch = relationship("Branch")

