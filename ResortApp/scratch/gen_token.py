from app.utils import auth
from datetime import timedelta
from app.database import SessionLocal
from app.models.user import User

db = SessionLocal()
user = db.query(User).filter(User.email == "anan@gmail.com").first()

if user:
    token_data = {
        "user_id": user.id, 
        "role": user.role.name,
        "branch_id": user.branch_id,
        "is_superadmin": getattr(user, 'is_superadmin', False),
        "permissions": user.role.permissions_list
    }
    token = auth.create_access_token(data=token_data)
    print(token)
else:
    print("User not found")
db.close()
