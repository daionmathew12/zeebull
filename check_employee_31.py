import sys
sys.path.insert(0, '/var/www/inventory/ResortApp')

from app.database import SessionLocal
from app.models.employee import Employee
from app.models.user import User

db = SessionLocal()

# Check if employee 31 exists
emp = db.query(Employee).filter(Employee.id == 31).first()
print(f"Employee 31: {emp}")

# Check all employees
employees = db.query(Employee).all()
print(f"\nTotal employees: {len(employees)}")
for e in employees[:15]:
    user_id = e.user_id if hasattr(e, 'user_id') else 'N/A'
    print(f"  ID: {e.id}, Name: {e.name}, User ID: {user_id}")

# Check users
users = db.query(User).all()
print(f"\nTotal users: {len(users)}")
for u in users[:15]:
    print(f"  ID: {u.id}, Email: {u.email}, Name: {u.name}")

db.close()
