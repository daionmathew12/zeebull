
from app.database import SessionLocal
from app.schemas.user import RoleCreate, RoleOut
from app.curd import role as crud_role
import json

db = SessionLocal()
try:
    # 1. Create RoleCreate object
    perms_json = json.dumps(["/dashboard"])
    role_in = RoleCreate(name="test_role_999", permissions=perms_json)
    
    # 2. Call CRUD
    print("Calling CRUD...")
    db_role = crud_role.create_role(db, role_in)
    print(f"CRUD returned role id: {db_role.id}, permissions type: {type(db_role.permissions)}")
    
    # 3. Simulate FastAPI response validation
    print("Validating response schema...")
    role_out = RoleOut.model_validate(db_role)
    print("Validation SUCCESS!")
    print(role_out)
    
    # Cleanup
    # crud_role.delete_role(db, db_role.id)

except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"FAILED: {e}")
finally:
    db.close()
