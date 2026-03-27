from app.database import SessionLocal
from app.models.employee import Employee
from app.models.user import User

db = SessionLocal()
emps = db.query(Employee).all()
for e in emps:
    u = db.query(User).get(e.user_id) if e.user_id else None
    print(f"Emp ID: {e.id}, Name: {e.name}, Email: {u.email if u else 'N/A'}")
db.close()
