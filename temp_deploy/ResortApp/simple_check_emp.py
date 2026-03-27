from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Employee

def check_employees():
    db = SessionLocal()
    try:
        employees = db.query(Employee).all()
        print(f"Found {len(employees)} employees")
        for emp in employees:
            print(f"ID: {emp.id}, Name: {emp.name}, UserID: {emp.user_id}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_employees()
