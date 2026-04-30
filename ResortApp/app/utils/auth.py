from datetime import timezone, datetime, timedelta
from jose import JWTError, jwt
import bcrypt
from app.models.user import User
from sqlalchemy.orm import Session, joinedload
from fastapi import Depends, HTTPException, status, Request
from typing import Optional, List, Any
from app.database import SessionLocal
from fastapi.security import OAuth2PasswordBearer
import os

# ENV
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "24"))

# Removed pwd_context - using bcrypt directly
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_password_hash(password):
    # Use bcrypt directly to avoid compatibility issues
    password_bytes = password.encode("utf-8")
    # bcrypt handles truncation automatically, but we'll limit to 72 bytes to be safe
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]

    # Generate salt and hash password using bcrypt directly
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain, hashed):
    # Use bcrypt directly to avoid compatibility issues
    password_bytes = plain.encode("utf-8")
    # bcrypt handles truncation automatically, but we'll limit to 72 bytes to be safe
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]

    # Verify password using bcrypt directly
    return bcrypt.checkpw(password_bytes, hashed.encode("utf-8"))


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=100))
    to_encode.update({"exp": expire})
    encoded = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    # Handle both string and bytes return from jwt.encode (version compatibility)
    return encoded.decode('utf-8') if isinstance(encoded, bytes) else encoded


def decode_token(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    # Support token as query parameter for PDF downloads/prints from mobile
    if not token:
        token = request.query_params.get("token")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Debug Logging
        # print(f"[AUTH DEBUG] Verifying token: {token[:10]}...")
        
        # Check if token is None or empty
        if not token:
            print("[AUTH DEBUG] Token is missing")
            raise credentials_exception
        
        payload = decode_token(token)
        # print(f"[AUTH DEBUG] Decoded payload: {payload}")
        
        user_id: int = payload.get("user_id")
        if user_id is None:
            print("[AUTH DEBUG] user_id missing in payload")
            raise credentials_exception
            
    except HTTPException:
        raise
    except JWTError as e:
        print(f"[AUTH DEBUG] JWT Error: {e}")
        raise credentials_exception
    except Exception as e:
        import traceback
        print(f"[AUTH DEBUG] Token Decode Error: {str(e)}\n{traceback.format_exc()}")
        raise credentials_exception

    try:
        user = db.query(User).options(joinedload(User.role)).filter(User.id == user_id).first()
        if user is None:
            print(f"[AUTH DEBUG] User ID {user_id} not found in database")
            raise credentials_exception
            
        if user.role is None:
            print(f"[AUTH DEBUG] User {user_id} has no role assigned")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User role not found. Please contact administrator."
            )
            
        # Store user info in request state for logging and scoping
        request.state.user_id = user.id
        request.state.branch_id = user.branch_id
        request.state.is_superadmin = getattr(user, 'is_superadmin', False)

        
        # print(f"[AUTH DEBUG] User verified: {user.email}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[AUTH DEBUG] DB Error during auth: {str(e)}\n{traceback.format_exc()}")
        raise credentials_exception



def get_branch_id(
    request: Request,
    current_user: User = Depends(get_current_user)
) -> Optional[int]:
    # 1. If superadmin, allow override via header or query param
    if getattr(current_user, 'is_superadmin', False):
        branch_header = request.headers.get("X-Branch-ID")
        if branch_header == "all":
            return None
        if branch_header: 
            try:
                return int(branch_header)
            except ValueError:
                pass
        
        # If superadmin didn't provide a branch_header or is unassigned, permit returning None/their branch_id
        return getattr(current_user, 'branch_id', None)
    
    # 2. Otherwise, return user's fixed branch_id
    if getattr(current_user, 'branch_id', None) is None:
        raise HTTPException(status_code=403, detail="User not assigned to a branch")
    return current_user.branch_id

def verify_superadmin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure the current user is a superadmin."""
    if not getattr(current_user, 'is_superadmin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin privileges required to perform this action."
        )
    return current_user

def has_permission(user: User, required_permission: str) -> bool:
    """
    Check if a user has a specific permission.
    Superadmins and 'admin' roles bypass all checks.
    Otherwise, checks against the role's parsed permissions_list.
    """
    if getattr(user, 'is_superadmin', False):
        return True
        
    if user.role:
        if user.role.name.lower() in ["admin", "superadmin"]:
            return True
            
        # permissions_list is a property on Role that returns a list of strings
        perms = getattr(user.role, "permissions_list", [])
        print(f"[DEBUG-AUTH] Checking permission '{required_permission}' for user {user.email}")
        print(f"[DEBUG-AUTH] Role: {user.role.name}, Permissions: {perms}")
        
        # 1. Exact match (e.g., "rooms:create")
        if required_permission in perms:
            return True
            
        # 2. Module wildcard match (if required_permission is "rooms", match if any permission starts with "rooms:")
        # This is useful for high-level visibility or broad access 
        if any(p.startswith(f"{required_permission}:") or p.startswith(f"{required_permission}_") for p in perms):
            return True
            
    return False

def require_permission(permission: str):
    """
    FastAPI dependency that ensures the current user has the required permission.
    Usage: Depends(require_permission("rooms:view"))
    """
    def permission_checker(current_user: User = Depends(get_current_user)):
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission} required."
            )
        return current_user
    return permission_checker
