import sys
from app.database import SessionLocal
from app.models.employee import Employee
from app.utils.auth import create_access_token
db = SessionLocal()
emp = db.query(Employee).filter(Employee.id==15).first()
if not emp or not emp.user:
    print("Error: No employee 15 or missing user")
    sys.exit(1)
access_token = create_access_token(data={'sub': emp.user.email})
print(access_token)
