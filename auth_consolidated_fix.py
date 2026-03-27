from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import SessionLocal, get_db
from app.schemas.auth import LoginRequest, Token
from app.utils import auth
from app.curd import user as crud_user
from app.utils.auth import get_current_user
from app.models.employee import Employee
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    try:
        # Check if user exists
        user = crud_user.get_user_by_email(db, request.email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Account is inactive. Please contact administrator.")
        
        # Check if user has a role
        if not user.role:
            raise HTTPException(status_code=400, detail="User role not assigned. Please contact administrator.")
        
        # Verify password
        if not auth.verify_password(request.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Get employee record if exists
        employee = db.query(Employee).filter(Employee.user_id == user.id).first()
        employee_id = employee.id if employee else None
        
        # Create access token
        # ENSURE is_superadmin is explicitly included as a boolean
        is_superadmin = getattr(user, 'is_superadmin', False)
        
        token_data = {
            "user_id": user.id, 
            "role": user.role.name,
            "branch_id": user.branch_id,
            "is_superadmin": bool(is_superadmin),
            "permissions": user.role.permissions_list if user.role else []
        }
        if employee_id:
            token_data["employee_id"] = employee_id

        access_token = auth.create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
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
    db: Session = Depends(get_db)
):
    """Get the current authenticated user's profile with employee details"""
    try:
        # Get employee record if exists
        employee = db.query(Employee).filter(Employee.user_id == user.id).first()
        
        response = {
            "id": user.id,
            "email": user.email,
            "role": user.role.name if user.role else "user",
            "branch_id": user.branch_id,
            "is_superadmin": getattr(user, 'is_superadmin', False),
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
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch profile: {str(e)}")
