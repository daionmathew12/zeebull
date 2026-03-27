from app.database import SessionLocal
from app.models.user import User, Role
from app.models.employee import Employee

db = SessionLocal()
try:
    email = 'housekeeping@orchid.com'
    user = db.query(User).filter(User.email == email).first()
    if not user:
        print(f"User with email {email} NOT found.")
    else:
        print(f"User found: ID={user.id}, Email={user.email}, RoleID={user.role_id}, IsActive={user.is_active}")
        role = db.query(Role).filter(Role.id == user.role_id).first()
        if role:
            print(f"Role: {role.name}")
        
        employee = db.query(Employee).filter(Employee.user_id == user.id).first()
        if employee:
            print(f"Employee found: ID={employee.id}, Name={employee.name}, Role={employee.role}")
        else:
            print("No Employee record linked to this User.")
finally:
    db.close()
