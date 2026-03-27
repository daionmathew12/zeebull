
from app.database import SessionLocal
from app.models.user import User, Role
from app.models.employee import Employee
from datetime import date

db = SessionLocal()
try:
    hk_role = db.query(Role).filter(Role.name == "housekeeping").first()
    if hk_role:
        # Assign another user
        user = db.query(User).filter(User.name == "new test").first()
        if user:
            user.role_id = hk_role.id
            emp = db.query(Employee).filter(Employee.user_id == user.id).first()
            if not emp:
                emp = Employee(name=user.name, role="housekeeping", salary=14000, join_date=date.today(), user_id=user.id)
                db.add(emp)
            else:
                emp.role = "housekeeping"
            db.commit()
            print(f"Updated {user.name} to housekeeping")
except Exception as e:
    db.rollback()
    print(f"Error: {e}")
finally:
    db.close()
