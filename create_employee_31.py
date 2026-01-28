import sys
sys.path.insert(0, '/var/www/inventory/ResortApp')

from app.database import SessionLocal
from app.models.employee import Employee
from app.models.user import User
from datetime import date

db = SessionLocal()

# Find the user "Alphi"
alphi_user = db.query(User).filter(User.name.ilike('%alphi%')).first()
if not alphi_user:
    # Try by email
    alphi_user = db.query(User).filter(User.email.ilike('%alphi%')).first()

if alphi_user:
    print(f"Found user: ID={alphi_user.id}, Email={alphi_user.email}, Name={alphi_user.name}")
    
    # Check if employee already exists for this user
    existing_emp = db.query(Employee).filter(Employee.user_id == alphi_user.id).first()
    if existing_emp:
        print(f"Employee already exists: ID={existing_emp.id}")
    else:
        # Create employee record with ID 31
        new_employee = Employee(
            id=31,
            name="Alphi",
            user_id=alphi_user.id,
            email=alphi_user.email,
            phone="",
            role="manager",
            join_date=date(2024, 1, 1),
            salary=50000.0,
            status="active"
        )
        db.add(new_employee)
        db.commit()
        print(f"Created employee ID 31 for user {alphi_user.email}")
else:
    print("User 'Alphi' not found. Listing all users:")
    users = db.query(User).all()
    for u in users:
        print(f"  ID: {u.id}, Email: {u.email}, Name: {u.name}")

db.close()
