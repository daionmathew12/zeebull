import logging
from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User as UserModel
from app.schemas.auth import Token
from app.utils.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is superadmin
    is_superadmin = getattr(user, "is_superadmin", False)
    
    # Create the token payload
    token_data = {
        "sub": user.email,
        "role": user.role.name if user.role else "user",
        "email": user.email,
        "name": user.name,
        "is_superadmin": bool(is_superadmin) # Explicitly cast to bool for JSON
    }

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data=token_data, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_data": {
            "email": user.email,
            "name": user.name,
            "role": user.role.name if user.role else "user",
            "is_superadmin": bool(is_superadmin)
        }
    }

@router.get("/profile")
async def get_profile(current_user: UserModel = Depends(get_current_user)):
    return {
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role.name if current_user.role else "user",
        "is_superadmin": getattr(current_user, "is_superadmin", False)
    }
