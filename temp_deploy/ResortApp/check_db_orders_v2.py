from app.database import SessionLocal
from app.models.foodorder import FoodOrder
from app.models.user import User
from app.models.employee import Employee
from sqlalchemy.orm import joinedload
from datetime import datetime

def check():
    db = SessionLocal()
    print(f"Current Server Time: {datetime.utcnow()}")
    
    # Check User kk
    u = db.query(User).options(joinedload(User.role)).filter(User.name == "kk").first()
    if u:
        print(f"User: {u.id}, Name: {u.name}, Role: {u.role.name if u.role else 'N/A'}")
        emp = db.query(Employee).filter(Employee.user_id == u.id).first()
        if emp:
            print(f"Employee ID: {emp.id}, Role: {emp.role}")
            
    # Check ALL Orders
    orders = db.query(FoodOrder).order_by(FoodOrder.id.desc()).limit(5).all()
    for o in orders:
        print(f"Order {o.id}: CreatedAt={o.created_at}, Assigned={o.assigned_employee_id}, CreatedBy={o.created_by_id}, PreparedBy={o.prepared_by_id}, Status={o.status}")

if __name__ == "__main__":
    check()
