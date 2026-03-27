from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.user import RoleCreate, RoleOut
from app.curd import role as crud_role
from app.models.user import User
from app.utils.auth import get_current_user
from app.utils.branch_scope import get_branch_id
from typing import Optional

router = APIRouter(prefix="/roles", tags=["Roles"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_role_permission(user: User):
    if getattr(user, "is_superadmin", False):
        return True
    if user.role and user.role.name.lower() in ["admin", "superadmin"]:
        return True
    raise HTTPException(status_code=403, detail="Only admin or superadmin can perform this action")

@router.post("", response_model=RoleOut)
def create_new_role(role: RoleCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_role_permission(user)
    try:
        return crud_role.create_role(db, role, branch_id=None)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.post("/", response_model=RoleOut)  # Handle trailing slash
def create_new_role_slash(role: RoleCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_role_permission(user)
    return crud_role.create_role(db, role, branch_id=None)

@router.get("", response_model=list[RoleOut])
def list_roles(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), skip: int = 0, limit: int = 100):
    roles = crud_role.get_roles(db, skip=skip, limit=limit, branch_id=None)
    return roles

@router.put("/{role_id}", response_model=RoleOut)
def update_existing_role(role_id: int, role: RoleCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_role_permission(user)
    updated_role = crud_role.update_role(db, role_id, role, branch_id=None)
    if not updated_role:
        raise HTTPException(status_code=404, detail="Role not found")
    return updated_role

@router.delete("/{role_id}")
def delete_existing_role(role_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    check_role_permission(user)
    success = crud_role.delete_role(db, role_id, branch_id=None)
    if not success:
        raise HTTPException(status_code=404, detail="Role not found")
    return {"message": "Role deleted successfully"}
