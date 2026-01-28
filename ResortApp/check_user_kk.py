from app.database import SessionLocal
from app import models as m

def check():
    db = SessionLocal()
    # Find user 'kk'
    u = db.query(m.User).filter(m.User.name == "kk").first()
    if not u:
        print("User 'kk' not found")
        return
    
    print(f"USER_ID_FOUND: {u.id}")
    print(f"USER_NAME_FOUND: {u.name}")
    print(f"USER_ROLE_ID: {u.role_id}")
    
    if u.role:
        print(f"USER_ROLE_NAME: {u.role.name}")
    else:
        print("USER_HAS_NO_ROLE")

    emp = db.query(m.Employee).filter(m.Employee.user_id == u.id).first()
    if emp:
        print(f"EMP_ID_FOUND: {emp.id}")
        print(f"EMP_NAME_FOUND: {emp.name}")
        print(f"EMP_ROLE_COL: {emp.role}")
    else:
        print("EMP_NOT_FOUND_FOR_USER")

    # Count food orders
    count = db.query(m.FoodOrder).count()
    print(f"TOTAL_FOOD_ORDERS: {count}")
    
    # Last 5
    last = db.query(m.FoodOrder).order_by(m.FoodOrder.id.desc()).limit(5).all()
    for o in last:
        print(f"ORDER_{o.id}: status={o.status}, created={o.created_at}")

if __name__ == "__main__":
    check()
