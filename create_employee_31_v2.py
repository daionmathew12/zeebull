import sys
sys.path.insert(0, '/var/www/inventory/ResortApp')

from app.database import SessionLocal
from app.models.employee import Employee
from app.models.user import User
from datetime import date

db = SessionLocal()

# Find all users to see who might be Alphi
print("All users:")
users = db.query(User).all()
for u in users:
    print(f"  ID: {u.id}, Email: {u.email}, Name: {u.name}")

# Check if employee 31 exists
emp31 = db.query(Employee).filter(Employee.id == 31).first()
if emp31:
    print(f"\nEmployee 31 already exists: {emp31.name}")
else:
    print("\nEmployee 31 does not exist. Creating it...")
    
    # Find a user to link to (preferably one without an employee record)
    # Let's find users without employees
    users_with_employees = [e.user_id for e in db.query(Employee).all() if e.user_id]
    users_without_employees = [u for u in users if u.id not in users_with_employees]
    
    print(f"Users without employee records: {[u.email for u in users_without_employees]}")
    
    # Create employee 31 - link to first available user or create standalone
    if users_without_employees:
        target_user = users_without_employees[0]
        print(f"Linking to user: {target_user.email}")
        user_id = target_user.id
    else:
        print("No available users, creating standalone employee")
        user_id = None
    
    new_employee = Employee(
        id=31,
        name="Alphi",
        role="manager",
        salary=50000.0,
        join_date=date(2024, 1, 1),
        user_id=user_id
    )
    db.add(new_employee)
    db.commit()
    print(f"✓ Created employee ID 31")

db.close()
