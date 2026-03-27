from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
import uuid
from app.database import get_db
from app.schemas.branch import Branch, BranchCreate, BranchUpdate
from app.curd import branch as branch_crud
from app.utils.auth import get_current_user, verify_superadmin
from app.models.user import User

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def save_upload_file(file: UploadFile, prefix: str) -> str:
    if not file or not file.filename:
        return ""
    file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    unique_filename = f"{prefix}_{uuid.uuid4().hex}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return f"/uploads/{unique_filename}"

router = APIRouter()

# For simplicity, we'll allow all authenticated users to see the branch list 
# so they can select their branch, but restrict creation/updates to admins.

@router.get("/branches", response_model=List[Branch])
def get_branches(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all branches."""
    # Only superadmins can request inactive branches
    if include_inactive and not getattr(current_user, 'is_superadmin', False):
        include_inactive = False
        
    return branch_crud.get_branches(db, skip=skip, limit=limit, include_inactive=include_inactive)

@router.get("/branches/{branch_id}", response_model=Branch)
def get_branch_by_id(
    branch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get details for a specific branch."""
    db_branch = branch_crud.get_branch_by_id(db, branch_id)
    if not db_branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    return db_branch

@router.post("/branches", response_model=Branch)
async def create_branch(
    name: str = Form(...),
    code: str = Form(...),
    address: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    gst_number: Optional[str] = Form(None),
    facebook: Optional[str] = Form(None),
    instagram: Optional[str] = Form(None),
    twitter: Optional[str] = Form(None),
    linkedin: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    admin: User = Depends(verify_superadmin) # Only superadmin can create branches
):
    """Create a new branch (Super Admin only)."""
        
    # Check if code already exists
    existing = branch_crud.get_branch_by_code(db, code)
    if existing:
        raise HTTPException(status_code=400, detail="Branch code already exists")
    
    image_url = None
    if image:
        image_url = await save_upload_file(image, "branch")
        
    return branch_crud.create_branch(
        db, 
        name=name, 
        code=code, 
        address=address, 
        phone=phone, 
        email=email, 
        gst_number=gst_number,
        image_url=image_url,
        facebook=facebook,
        instagram=instagram,
        twitter=twitter,
        linkedin=linkedin
    )

@router.put("/branches/{branch_id}", response_model=Branch)
async def update_branch(
    branch_id: int,
    name: Optional[str] = Form(None),
    code: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    gst_number: Optional[str] = Form(None),
    facebook: Optional[str] = Form(None),
    instagram: Optional[str] = Form(None),
    twitter: Optional[str] = Form(None),
    linkedin: Optional[str] = Form(None),
    is_active: Optional[bool] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    admin: User = Depends(verify_superadmin) # Only superadmin can update branches
):
    """Update a branch (Super Admin only)."""
    
    update_data = {}
    if name is not None: update_data["name"] = name
    if code is not None: update_data["code"] = code
    if address is not None: update_data["address"] = address
    if phone is not None: update_data["phone"] = phone
    if email is not None: update_data["email"] = email
    if gst_number is not None: update_data["gst_number"] = gst_number
    if facebook is not None: update_data["facebook"] = facebook
    if instagram is not None: update_data["instagram"] = instagram
    if twitter is not None: update_data["twitter"] = twitter
    if linkedin is not None: update_data["linkedin"] = linkedin
    if is_active is not None: update_data["is_active"] = is_active
    
    if image:
        update_data["image_url"] = await save_upload_file(image, "branch")
        
    updated = branch_crud.update_branch(db, branch_id, **update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Branch not found")
    return updated

@router.delete("/branches/{branch_id}")
def delete_branch(
    branch_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_superadmin) # Only superadmin can delete branches
):
    """Deactivate a branch (Super Admin only)."""
        
    success = branch_crud.delete_branch(db, branch_id)
    if not success:
        raise HTTPException(status_code=404, detail="Branch not found")
    return {"message": "Branch deactivated successfully"}

@router.patch("/branches/{branch_id}/toggle-status", response_model=Branch)
def toggle_branch_status(
    branch_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_superadmin) # Only superadmin can toggle branches
):
    """Toggle branch active status."""
    db_branch = branch_crud.get_branch_by_id(db, branch_id)
    if not db_branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    
    db_branch.is_active = not db_branch.is_active
    db.commit()
    db.refresh(db_branch)
    return db_branch
