from app.database import SessionLocal
from app.api.service_request import get_service_requests
from app.models.user import User

db = SessionLocal()
# Mock a superadmin user
user = db.query(User).first()
user.role.name = "admin" # fake it if needed or just let it pass
try:
    print("User:", user.email, user.role.name)
    res = get_service_requests(skip=0, limit=100, status=None, room_id=6, include_checkout_requests=True, db=db, current_user=user, branch_id=1)
    print("Result:", res)
except Exception as e:
    import traceback
    traceback.print_exc()
