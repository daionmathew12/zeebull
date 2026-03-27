import sys
import os
import asyncio
import json

# Add ResortApp to path
sys.path.append(os.path.join(os.getcwd(), 'ResortApp'))

from app.database import SessionLocal
from app.models.user import User
from app.models.service import Service
from app.curd import service as service_crud

def test_create_global_service():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == 1).first()
        print(f"Creating service as user: {user.name} (Superadmin: {user.is_superadmin})")
        
        # Simulate creating a service in 'Enterprise View' (branch_id=None)
        try:
            # We call the CRUD directly since the API dependency has already been resolved to None
            new_service = service_crud.create_service(
                db=db,
                name="Enterprise Service Test",
                description="This service was created in All Branches view",
                charges=150.0,
                branch_id=None # This is what happens in All Branch view
            )
            print(f"Success! Service Created with ID: {new_service.id}, Branch: {new_service.branch_id}")
        except Exception as e:
            print(f"Failed to create service: {e}")
            import traceback
            traceback.print_exc()
            
    finally:
        db.close()

if __name__ == "__main__":
    test_create_global_service()
