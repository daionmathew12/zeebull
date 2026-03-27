from sqlalchemy.orm import Session
from app.models.user import User, Role
from app.schemas.user import UserCreate
import bcrypt
from app.utils import auth


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user: UserCreate):
    # Use bcrypt directly to avoid compatibility issues
    password_bytes = user.password.encode("utf-8")
    # bcrypt handles truncation automatically, but we'll limit to 72 bytes to be safe
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]

    # Generate salt and hash password using bcrypt directly
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt).decode("utf-8")
    db_user = User(
        name=user.name,
        email=user.email,
        phone=user.phone,
        hashed_password=hashed_password,
        role_id=user.role_id,
        branch_id=user.branch_id,
        is_superadmin=user.is_superadmin,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return None
    # Check if user is active
    if not user.is_active:
        return None
    # Verify password
    try:
        if not auth.verify_password(password, user.hashed_password):
            return None
    except Exception as e:
        print(f"Password verification error for {email}: {str(e)}")
        return None
    return user
