from ast import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.user import UserCreate, UserOut, AdminSetupRequest, RoleCreate
from app.curd import user as crud_user
from app.curd import role as crud_role
from app.utils.auth import get_current_user, verify_superadmin
from app.models.user import User, Role
from sqlalchemy.orm import joinedload


router = APIRouter(prefix="/users", tags=["Users"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
@router.get("/me", response_model=UserOut)
def read_current_user(current_user = Depends(get_current_user)):
    return current_user
@router.post("", response_model=UserOut)
def register_user(
    user: UserCreate, 
    db: Session = Depends(get_db),
    admin: User = Depends(verify_superadmin) # Only superadmin can create users natively
):
    db_user = crud_user.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud_user.create_user(db=db, user=user)

@router.post("/setup-admin", response_model=UserOut, summary="One-time Admin User Setup")
def setup_initial_admin(setup_data: AdminSetupRequest, db: Session = Depends(get_db)):
    """
    Creates the first admin user and the 'admin' role.
    This endpoint will only work if there are no users in the database.
    """
    # 1. Check if any user already exists.
    if db.query(User).first():
        raise HTTPException(status_code=403, detail="Admin setup has already been completed.")

    # 2. Find or create the 'admin' role with all permissions.
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if not admin_role:
        admin_role_schema = RoleCreate(name="admin", permissions='["*"]')
        admin_role = crud_role.create_role(db, admin_role_schema)

    # 3. Create the admin user.
    user_data = UserCreate(
        email=setup_data.email,
        password=setup_data.password,
        name=setup_data.name,
        phone=None, # Phone is optional
        role_id=admin_role.id,
    )
    
    new_admin_user = crud_user.create_user(db=db, user=user_data)
    return new_admin_user

from app.utils.branch_scope import get_branch_id

def _get_users_impl(db: Session, current_user: User, branch_id: int = None, skip: int = 0, limit: int = 20):
    """Helper function for get_users"""
    query = db.query(User).options(joinedload(User.role))
    if branch_id is not None:
        query = query.filter(User.branch_id == branch_id)
    return query.offset(skip).limit(limit).all()

@router.get("")
def get_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), branch_id: int = Depends(get_branch_id), skip: int = 0, limit: int = 20):
    return _get_users_impl(db, current_user, branch_id, skip, limit)

@router.get("/")  # Handle trailing slash
def get_users_slash(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), branch_id: int = Depends(get_branch_id), skip: int = 0, limit: int = 20):
    return _get_users_impl(db, current_user, branch_id, skip, limit)
