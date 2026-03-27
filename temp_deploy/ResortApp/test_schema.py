
from app.schemas.user import RoleOut
from pydantic import ValidationError
import json

class MockDBRole:
    def __init__(self, id, name, permissions):
        self.id = id
        self.name = name
        self.permissions = permissions

try:
    # Simulate DB role with JSON string permissions
    perms_str = json.dumps(["/dashboard", "/account"])
    db_role = MockDBRole(id=1, name="manager", permissions=perms_str)
    
    # Try to validate
    role_out = RoleOut.model_validate(db_role)
    print("Validation SUCCESS")
    print(role_out)
except Exception as e:
    print("Validation ALL FAILED")
    print(e)
