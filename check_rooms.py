
from app.utils.auth import get_db
from app.models.room import Room

db = next(get_db())

print("--- BRANCH 1 ROOMS ---")
rooms = db.query(Room).filter(Room.branch_id == 1).all()
for r in rooms:
    print(f"ID: {r.id}, Number: {r.number}, Branch: {r.branch_id}")
