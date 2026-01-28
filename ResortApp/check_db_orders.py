from app.database import SessionLocal
from app.models.foodorder import FoodOrder
from app.models.user import User
from app.models.employee import Employee
from sqlalchemy.orm import joinedload

def check():
    db = SessionLocal()
    print("--- Database Check ---")
    
    # Check User kk
    u = db.query(User).filter(User.name == "kk").first()
    if u:
        print(f"User: {u.id}, Name: {u.name}, Role: {u.role.name if u.role else 'N/A'}")
        emp = db.query(Employee).filter(Employee.user_id == u.id).first()
        if emp:
            print(f"Employee: {emp.id}, Name: {emp.name}, Role: {emp.role}")
            
    # Check Orders 1 and 2
    for oid in [1, 2]:
        o = db.query(FoodOrder).get(oid)
        if o:
            print(f"Order {o.id}: CreatedAt={o.created_at}, AssignedEmpID={o.assigned_employee_id}, PreparedBy={o.prepared_by_id}, CreatedBy={o.created_by_id}, Status={o.status}")
        else:
            print(f"Order {oid} not found")

if __name__ == "__main__":
    check()
