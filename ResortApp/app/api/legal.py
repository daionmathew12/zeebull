from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Header
from fastapi.responses import FileResponse
import os
# Absolute project root path (ResortApp/)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_UPLOAD_ROOT = os.path.join(_BASE_DIR, "uploads")
from sqlalchemy.orm import Session
from typing import List, Optional, Any
import shutil
from datetime import datetime
from app.utils.date_utils import get_ist_now, get_ist_today
from app.database import get_db
from app.utils.auth import get_current_user
from app.models.legal import LegalDocument
from app.models.branch import Branch
from pydantic import BaseModel

router = APIRouter()

# Ensure upload directory exists
UPLOAD_DIR = os.path.join(_UPLOAD_ROOT, "legal")
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
    current_user: Any = Depends(get_current_user),
    x_branch_id: Optional[str] = Header(None)
):
    print(f"[DEBUG] Uploading legal document: {name} for branch {x_branch_id}")
    # Generate unique filename
    timestamp = get_ist_now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Determine branch
    branch_id = 1 # Fallback
    if x_branch_id and x_branch_id != "all":
        branch_id = int(x_branch_id)
    elif hasattr(current_user, "branch_id"):
        branch_id = current_user.branch_id

    # Store relative path for static serving
    relative_path = f"uploads/legal/{filename}"
    print(f"[DEBUG-UPLOAD] Storing path: '{relative_path}'")

    db_document = LegalDocument(
        name=name,
        document_type=document_type,
        file_path=relative_path, # Store relative path
        description=description,
        branch_id=branch_id
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    print(f"[DEBUG-UPLOAD] Final DB file_path: '{db_document.file_path}'")
    
    return db_document

@router.get("/", response_model=List[LegalDocumentResponse])
def get_legal_documents(
    db: Session = Depends(get_db), 
    current_user: Any = Depends(get_current_user),
    x_branch_id: Optional[str] = Header(None)
):
    print(f"[DEBUG] Fetching legal documents. User role: {getattr(current_user.role, 'name', 'N/A')}, Branch header: {x_branch_id}")
    query = db.query(LegalDocument)
    
    user_role = getattr(current_user.role, "name", "").lower() if current_user.role else ""
    
    if user_role == "superadmin" or getattr(current_user, "is_superadmin", False):
        if x_branch_id and x_branch_id != 'all':
            query = query.filter(LegalDocument.branch_id == int(x_branch_id))
    else:
        query = query.filter(LegalDocument.branch_id == current_user.branch_id)
    
    docs = query.order_by(LegalDocument.uploaded_at.desc()).all()
    
    # Normalize paths for frontend (backward compatibility for absolute paths)
    base_dir_norm = _BASE_DIR.lower().replace('\\', '/')
    print(f"[DEBUG-LIST] Base dir normalized: {base_dir_norm}")
    for doc in docs:
        if not doc.file_path:
            continue
            
        print(f"[DEBUG-LIST] ID={doc.id} Incoming path: {doc.file_path}")
        path_norm = doc.file_path.replace('\\', '/')
        # Check if it's an absolute Windows path
        if os.path.isabs(doc.file_path) or path_norm.startswith('C:/') or path_norm.startswith('c:/'):
            # Try to make it relative to base_dir (case-insensitive)
            if base_dir_norm in path_norm.lower():
                start_idx = path_norm.lower().find(base_dir_norm)
                rel = path_norm[start_idx + len(base_dir_norm):].lstrip('/')
                doc.file_path = rel
            elif 'uploads/' in path_norm.lower():
                # Fallback: if it contains uploads/, just take everything from uploads/ onwards
                idx = path_norm.lower().find('uploads/')
                doc.file_path = path_norm[idx:]
        print(f"[DEBUG-LIST] ID={doc.id} Outgoing path: {doc.file_path}")
    
    print(f"[DEBUG] Found {len(docs)} documents")
    return docs

@router.delete("/{document_id}")
def delete_legal_document(document_id: int, db: Session = Depends(get_db), current_user: Any = Depends(get_current_user)):
    # Validate branch ownership
    document = db.query(LegalDocument).filter(LegalDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    user_role = getattr(current_user.role, "name", "").lower() if current_user.role else ""
    is_super = user_role == "superadmin" or getattr(current_user, "is_superadmin", False)

    if not is_super:
        if document.branch_id != current_user.branch_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this document")
    
    # Delete file from filesystem
    # Reconstruct absolute path for deletion
    if os.path.isabs(document.file_path):
        abs_path = document.file_path
    else:
        abs_path = os.path.join(_BASE_DIR, document.file_path)
        
    if os.path.exists(abs_path):
        try:
            os.remove(abs_path)
        except Exception as e:
            print(f"Error deleting file: {e}")
    
    db.delete(document)
    db.commit()
    return {"message": "Document deleted successfully"}

@router.get("/download/{document_id}")
def download_legal_document(
    document_id: int, 
    db: Session = Depends(get_db), 
    current_user: Any = Depends(get_current_user)
):
    document = db.query(LegalDocument).filter(LegalDocument.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Reconstruct absolute path
    if os.path.isabs(document.file_path):
        abs_path = document.file_path
    else:
        abs_path = os.path.join(_BASE_DIR, document.file_path)
        
    if not os.path.exists(abs_path):
        print(f"[DEBUG-DOWNLOAD] ERROR: File not found at {abs_path}") # Log error to console
        raise HTTPException(status_code=404, detail=f"File not found on server at {abs_path}")
        
    print(f"[DEBUG-DOWNLOAD] Serving file: {abs_path}")
    return FileResponse(
        path=abs_path,
        filename=os.path.basename(document.file_path),
        media_type='application/octet-stream'
    )
