from app.database import SessionLocal
from app import models as m
from sqlalchemy.orm import joinedload

def diagnose():
    db = SessionLocal()
    # 1. Identify User 'kk'
    user = db.query(m.User).options(joinedload(m.User.role)).filter(m.User.name == "kk").first()
    if not user:
        print("DIAGNOSE: User 'kk' not found.")
        return
    
    print(f"USER_ID: {user.id}")
    print(f"USER_ROLE: {user.role.name if user.role else 'NONE'}")
    
    # 2. Check Employee Record
    emp = db.query(m.Employee).filter(m.Employee.user_id == user.id).first()
    if emp:
        print(f"EMP_ID: {emp.id}")
        print(f"EMP_ROLE: {emp.role}")
    else:
        print("EMP_RECORD: Not found for this user.")

    # 3. Check RECENT Food Orders (all of them)
    print("\nRECENT_FOOD_ORDERS (Last 10):")
    orders = db.query(m.FoodOrder).order_by(m.FoodOrder.id.desc()).limit(10).all()
    for o in orders:
        print(f"ID: {o.id} | Status: {o.status} | CreatedAt: {o.created_at} | AssignedEmpID: {o.assigned_employee_id}")

    # 4. Check if any orders match this user/employee
    if emp:
        match_count = db.query(m.FoodOrder).filter(m.FoodOrder.assigned_employee_id == emp.id).count()
        print(f"\nORDERS_ASSIGNED_TO_EMP_{emp.id}: {match_count}")
    
    match_user_id = db.query(m.FoodOrder).filter(m.FoodOrder.assigned_employee_id == user.id).count()
    print(f"ORDERS_ASSIGNED_TO_USER_ID_{user.id}: {match_user_id}")

if __name__ == "__main__":
    diagnose()
