from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
import os
from datetime import datetime
from app.database import get_db
from app.utils.auth import get_current_user
from app.models.legal import LegalDocument
from pydantic import BaseModel

router = APIRouter()

# Ensure upload directory exists
UPLOAD_DIR = "uploads/legal"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class LegalDocumentResponse(BaseModel):
    id: int
    name: str
    document_type: Optional[str]
    file_path: str
    uploaded_at: datetime
    description: Optional[str]

    class Config:
        from_attributes = True

@router.post("/upload", response_model=LegalDocumentResponse)
async def upload_legal_document(
    file: UploadFile = File(...),
    name: str = Form(...),
    document_type: str = Form(None),
    description: str = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Create database record
    db_document = LegalDocument(
        name=name,
        document_type=document_type,
        file_path=file_path,
        description=description
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    return db_document

@router.get("/", response_model=List[LegalDocumentResponse])
def get_legal_documents(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    return db.query(LegalDocument).order_by(LegalDocument.uploaded_at.desc()).all()

@router.delete("/{document_id}")
def delete_legal_document(document_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    document = db.query(LegalDocument).filter(LegalDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file from filesystem
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    db.delete(document)
    db.commit()
    return {"message": "Document deleted successfully"}
