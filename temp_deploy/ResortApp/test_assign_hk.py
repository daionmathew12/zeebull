
from app.database import SessionLocal
from app.models.user import User, Role
from app.models.employee import Employee
from datetime import date

db = SessionLocal()
try:
    # Find a user to make housekeeping
    # Let's pick a 'guest' user if one exists
    guest_role = db.query(Role).filter(Role.name == "guest").first()
    hk_role = db.query(Role).filter(Role.name == "housekeeping").first()
    
    if not hk_role:
        print("Housekeeping role not found. Please run seed_roles.py first.")
    else:
        user = db.query(User).filter(User.email == "THEN@GMAIL.COM").first() # "mido" from previous truncated list
        if not user:
            user = db.query(User).filter(User.role_id == guest_role.id).first()
            
        if user:
            print(f"Updating user: {user.name} ({user.email}) to role 'housekeeping'")
            user.role_id = hk_role.id
            
            # Check if an employee record exists for this user, if not create one
            emp = db.query(Employee).filter(Employee.user_id == user.id).first()
            if not emp:
                print(f"Creating employee record for {user.name}")
                emp = Employee(
                    name=user.name,
                    role="housekeeping",
                    salary=15000,
                    join_date=date.today(),
                    user_id=user.id
                )
                db.add(emp)
            else:
                emp.role = "housekeeping"
                
            db.commit()
            print("Successfully updated.")
        else:
            print("No suitable user found to update.")
except Exception as e:
    db.rollback()
    print(f"Error: {e}")
finally:
    db.close()
