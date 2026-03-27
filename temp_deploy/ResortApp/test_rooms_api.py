
import requests

# We need a token. I'll try to find one or just use the DB to get a user and generate one if I could, 
# but I can just use the internal logic.
import psycopg2
from app.database import SessionLocal
from app.api.room import _get_rooms_impl
from app.models.user import User

db = SessionLocal()
try:
    # Use any admin user
    user = db.query(User).first()
    print(f"Using user: {user.email}")
    
    rooms = _get_rooms_impl(db, limit=1000)
    print(f"Fetched {len(rooms)} rooms")
    for r in rooms:
        print(f"Room {r.number}: ID={r.id}, Status={r.status}, Guest={r.current_guest_name}")
finally:
    db.close()
