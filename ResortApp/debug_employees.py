
import requests
import json
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.employee import Employee
from app.database import Base

# Local check
def check_local_employees():
    print("\n--- Checking Local Database ---")
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        employees = db.query(Employee).all()
        print(f"Found {len(employees)} employees in local DB.")
        for emp in employees:
            print(f"ID: {emp.id}, Name: {emp.name}, Role: {emp.role}")
        db.close()
    except Exception as e:
        print(f"Local DB Error: {e}")

# Production check
BASE_URL = "https://teqmates.com/orchidapi/api"
LOGIN_URL = f"{BASE_URL}/auth/login"
EMPLOYEES_URL = f"{BASE_URL}/employees"

EMAIL = "m@orchid.com"
PASSWORD = "1234"

def get_token():
    try:
        response = requests.post(LOGIN_URL, json={"email": EMAIL, "password": PASSWORD})
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"Login failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def check_prod_employees(token):
    headers = {"Authorization": f"Bearer {token}"}
    print(f"\n--- Checking Production API ({EMPLOYEES_URL}) ---")
    try:
        # Try getting all (limit=100)
        params = {"limit": 100}
        resp = requests.get(EMPLOYEES_URL, headers=headers, params=params)
        if resp.status_code == 200:
            employees = resp.json()
            print(f"Found {len(employees)} employees in production.")
            print(f"{'ID':<5} {'Name':<20} {'Role':<15} {'Status':<10}")
            print("-" * 55)
            for emp in employees:
                print(f"{emp['id']:<5} {emp['name']:<20} {emp['role']:<15} {emp.get('status', 'N/A'):<10}")
        else:
            print(f"Failed to get employees: {resp.status_code} - {resp.text}")
            
    except Exception as e:
        print(f"Prod API Error: {e}")

if __name__ == "__main__":
    check_local_employees()
    
    token = get_token()
    if token:
        check_prod_employees(token)
