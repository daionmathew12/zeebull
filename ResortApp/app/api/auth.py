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
        print(f"LOGIN DEBUG: Received email='{request.email}'")
        # Check if user exists
        user = crud_user.get_user_by_email(db, request.email)
        if not user:
            print(f"LOGIN DEBUG: User not found for email: '{request.email}'")
            raise HTTPException(status_code=400, detail="Invalid credentials")
        
        print(f"LOGIN DEBUG: User found: id={user.id}, active={user.is_active}, role={user.role}")
        
        # Check if user is active
        if not user.is_active:
            print(f"Login attempt: User {request.email} is inactive")
            raise HTTPException(status_code=400, detail="Account is inactive. Please contact administrator.")
        
        # Check if user has a role
        if not user.role:
            print(f"Login attempt: User {request.email} has no role assigned")
            raise HTTPException(status_code=400, detail="User role not assigned. Please contact administrator.")
        
        # Verify password
        try:
            password_valid = auth.verify_password(request.password, user.hashed_password)
        except Exception as pwd_error:
            print(f"Password verification error for {request.email}: {str(pwd_error)}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=400, detail="Invalid credentials")
        
        if not password_valid:
            print(f"Login attempt: Invalid password for email: {request.email}")
            raise HTTPException(status_code=400, detail="Invalid credentials")
        
        
        # Get employee record if exists
        employee = db.query(Employee).filter(Employee.user_id == user.id).first()
        employee_id = employee.id if employee else None
        
        # DEBUG LOGGING TO FILE
        try:
            with open("/tmp/auth_debug.log", "a") as f:
                f.write(f"\n--- Login Attempt {request.email} ---\n")
                f.write(f"DB URL: {str(db.bind.url)}\n")
                f.write(f"User ID: {user.id}\n")
                f.write(f"Employee Found: {employee}\n")
                f.write(f"Employee ID: {employee_id}\n")
        except Exception as log_err:
            print(f"Log Error: {log_err}")

        # Create access token
        token_data = {"user_id": user.id, "role": user.role.name}
        if employee_id:
            token_data["employee_id"] = employee_id
            
        access_token = auth.create_access_token(
            data=token_data,
            expires_delta=timedelta(hours=auth.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        print(f"Login successful: {request.email}, employee_id: {employee_id}")
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        # Re-raise HTTP exceptions (like invalid credentials)
        raise
    except Exception as e:
        # Log unexpected errors
        print(f"Login error for {request.email}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.get("/me")
def get_current_user_profile(
    user=Depends(get_current_user),
    db: Session = Depends(auth.get_db)
):
    """Get the current authenticated user's profile with employee details"""
    try:
        # Get employee record if exists
        employee = db.query(Employee).filter(Employee.user_id == user.id).first()
        
        response = {
            "id": user.id,
            "email": user.email,
            "role": user.role.name,
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
                "wellness_leave_balance": employee.wellness_leave_balance
            }
        
        return response
    except Exception as e:
        print(f"Error fetching user profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch profile: {str(e)}")


@router.get("/admin-only")
def admin_data(user=Depends(get_current_user)):
    if user.role.name != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    return {"message": "Admin access granted"}



