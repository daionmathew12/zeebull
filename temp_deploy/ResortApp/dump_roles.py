
from app.database import SessionLocal
from app.models.user import Role
import sys

# Redirect stdout to file
with open("roles_dump.txt", "w") as f:
    sys.stdout = f
    db = SessionLocal()
    try:
        roles = db.query(Role).all()
        print(f"COUNT: {len(roles)}")
        for r in roles:
            print(f"ID: {r.id}, NAME: '{r.name}'")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()
