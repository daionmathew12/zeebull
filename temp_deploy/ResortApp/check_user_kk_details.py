from app.database import SessionLocal
from app.models.user import User
from app.models.employee import Employee
from sqlalchemy.orm import joinedload

def check():
    db = SessionLocal()
    u = db.query(User).options(joinedload(User.role)).filter(User.name == "kk").first()
    if u:
        print(f"User ID: {u.id}")
        print(f"User Name: {u.name}")
        print(f"Role: {u.role.name if u.role else 'N/A'}")
        emp = db.query(Employee).filter(Employee.user_id == u.id).first()
        if emp:
            print(f"Employee ID: {emp.id}")
            print(f"Employee Role: {emp.role}")
if __name__ == "__main__":
    check()
