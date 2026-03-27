from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.schemas.branch import Branch, BranchCreate, BranchUpdate
from app.curd import branch as branch_crud
from app.utils.auth import get_current_user, verify_superadmin
from app.models.user import User

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
def create_branch(
    branch: BranchCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_superadmin) # Only superadmin can create branches
):
    """Create a new branch (Super Admin only)."""
        
    # Check if code already exists
    existing = branch_crud.get_branch_by_code(db, branch.code)
    if existing:
        raise HTTPException(status_code=400, detail="Branch code already exists")
        
    return branch_crud.create_branch(
        db, 
        name=branch.name, 
        code=branch.code, 
        address=branch.address, 
        phone=branch.phone, 
        email=branch.email, 
        gst_number=branch.gst_number
    )

@router.put("/branches/{branch_id}", response_model=Branch)
def update_branch(
    branch_id: int,
    branch_update: BranchUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_superadmin) # Only superadmin can update branches
):
    """Update a branch (Super Admin only)."""
        
    updated = branch_crud.update_branch(db, branch_id, **branch_update.dict(exclude_unset=True))
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
