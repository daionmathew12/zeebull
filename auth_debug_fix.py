from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import SessionLocal
from app.schemas.auth import LoginRequest, Token
from app.utils import auth
from app.curd import user as crud_user
from fastapi import Depends
from app.utils.auth import get_current_user
from app.models.employee import Employee


router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(request: LoginRequest, db: Session = Depends(auth.get_db)):
    try:
        user = crud_user.get_user_by_email(db, request.email)
        if not user:
            raise HTTPException(status_code=400, detail="Invalid credentials")
        
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Account is inactive. Please contact administrator.")
        
        if not user.role:
            raise HTTPException(status_code=400, detail="User role not assigned. Please contact administrator.")
        
        if not auth.verify_password(request.password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Invalid credentials")
        
        employee = db.query(Employee).filter(Employee.user_id == user.id).first()
        employee_id = employee.id if employee else None
        
        # Create access token with more info for frontend
        is_super = bool(user.is_superadmin)
        token_data = {
            "user_id": user.id, 
            "email": user.email,
            "name": user.name or user.email.split('@')[0],
            "role": user.role.name,
            "branch_id": user.branch_id,
            "is_superadmin": is_super,
            "permissions": user.role.permissions_list
        }
        if employee_id:
            token_data["employee_id"] = employee_id

        # LOG THE TOKEN DATA
        with open("/tmp/auth_debug.log", "a") as f:
            f.write(f"\n--- Login Attempt {user.email} ---\n")
            f.write(f"Token Data: {token_data}\n")
            f.write(f"is_superadmin from model: {user.is_superadmin}\n")

        access_token = auth.create_access_token(
            data=token_data,
            expires_delta=timedelta(hours=auth.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.get("/me")
def get_current_user_profile(
    user=Depends(get_current_user),
    db: Session = Depends(auth.get_db)
):
    try:
        employee = db.query(Employee).filter(Employee.user_id == user.id).first()
        is_super = bool(user.is_superadmin)
        
        response = {
            "id": user.id,
            "email": user.email,
            "name": user.name or user.email.split('@')[0],
            "role": user.role.name,
            "branch_id": user.branch_id,
            "is_superadmin": is_super,
            "permissions": user.role.permissions_list if user.role else [],
            "employee": None
        }

        if employee:
            response["employee"] = {
                "id": employee.id,
                "name": employee.name,
                "role": employee.role,
                "salary": employee.salary,
                "join_date": str(employee.join_date) if employee.join_date else None,
                "image_url": employee.image_url,
                "paid_leave_balance": employee.paid_leave_balance,
                "sick_leave_balance": employee.sick_leave_balance,
                "long_leave_balance": employee.long_leave_balance,
                "wellness_leave_balance": employee.wellness_leave_balance,
                "daily_tasks": employee.daily_tasks
            }
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch profile: {str(e)}")


@router.get("/admin-only")
def admin_data(user=Depends(get_current_user)):
    if user.role.name != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    return {"message": "Admin access granted"}
