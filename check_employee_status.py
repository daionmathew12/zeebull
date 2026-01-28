import sys
sys.path.insert(0, '/var/www/inventory/ResortApp')

from app.database import SessionLocal
from app.models.employee import Employee

db = SessionLocal()

# Get employee with id 31 (alphi)
emp = db.query(Employee).filter(Employee.id == 31).first()

if emp:
    print(f"Employee ID: {emp.id}")
    print(f"Name: {emp.name}")
    print(f"Role: {emp.role}")
    print(f"Salary: {emp.salary}")
    print(f"Join Date: {emp.join_date}")
    
    # Check if status attribute exists
    if hasattr(emp, 'status'):
        print(f"Status: {emp.status}")
    else:
        print("Status attribute does NOT exist in the model")
    
    # Print all attributes
    print("\nAll attributes:")
    for attr in dir(emp):
        if not attr.startswith('_') and not callable(getattr(emp, attr)):
            print(f"  {attr}: {getattr(emp, attr, 'N/A')}")
else:
    print("Employee 31 not found")

db.close()
