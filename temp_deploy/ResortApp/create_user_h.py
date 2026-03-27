from app.database import SessionLocal
from app.models.user import User, Role
from app.models.employee import Employee
from app.utils.auth import get_password_hash
import sys

def create_user(email, password, role_name="manager"):
    db = SessionLocal()
    try:
        # Check if role exists
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            print(f"Role {role_name} not found, creating it.")
            role = Role(name=role_name, permissions="[]")
            db.add(role)
            db.commit()
            db.refresh(role)
        
        # Check if user exists
        user = db.query(User).filter(User.email == email).first()
        if user:
            print(f"User {email} already exists. Updating password.")
            user.hashed_password = get_password_hash(password)
            db.commit()
            return
        
        # Create user
        new_user = User(
            name=email.split('@')[0],
            email=email,
            hashed_password=get_password_hash(password),
            role_id=role.id,
            is_active=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"User {email} created with role {role_name}.")
        
        # Create employee record
        employee = Employee(
            name=new_user.name.capitalize(),
            role=role_name.capitalize(),
            salary=50000.0,
            user_id=new_user.id
        )
        db.add(employee)
        db.commit()
        print(f"Employee record for {new_user.name} created.")
        
    finally:
        db.close()

if __name__ == "__main__":
    create_user("a@h.com", "1234")
