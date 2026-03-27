import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from dotenv import load_dotenv

sys.path.append(os.path.join(os.getcwd(), "ResortApp"))
load_dotenv(os.path.join(os.getcwd(), "ResortApp", ".env"))

from app.api.employee import _list_employees_impl
from app.models.user import User

engine = create_engine(os.getenv("DATABASE_URL"))
db = Session(bind=engine)

# Mock current_user
mock_user = User(id=1, email="admin@example.com", name="Admin")

print("--- Testing Employee Status for Branch 2 ---")
employees = _list_employees_impl(db, mock_user, branch_id=2)
for emp in employees:
    print(f"ID: {emp['id']}, Name: {emp['name']}, Status: {emp['status']}, Current Status: {emp['current_status']}")
