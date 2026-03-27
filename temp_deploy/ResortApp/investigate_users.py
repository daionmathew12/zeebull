
from app.database import SessionLocal
from app.models.user import User, Role
from app.models.employee import Employee

db = SessionLocal()
try:
    print("--- ROLES ---")
    roles = db.query(Role).all()
    for r in roles:
        print(f"ID: {r.id}, Name: '{r.name}'")

    print("\n--- HOUSEKEEPING USERS ---")
    hk_users = db.query(User).filter(User.role.has(Role.name.ilike('%housekeeping%'))).all()
    if not hk_users:
        print("No users found with housekeeping role.")
    for u in hk_users:
        print(f"ID: {u.id}, Name: {u.name}, Email: {u.email}, Role: {u.role.name}")

    print("\n--- ALL EMPLOYEES ---")
    emps = db.query(Employee).all()
    for e in emps:
        print(f"ID: {e.id}, Name: {e.name}, Role: {e.role}, UserID: {e.user_id}")

    print("\n--- USERS NAMED 'NEW TEST' ---")
    nt_users = db.query(User).filter(User.name.ilike('%new test%')).all()
    for u in nt_users:
        role_name = u.role.name if u.role else "None"
        print(f"ID: {u.id}, Name: {u.name}, Email: {u.email}, Role: {role_name}")

except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
