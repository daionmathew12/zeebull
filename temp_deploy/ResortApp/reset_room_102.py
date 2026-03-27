from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.room import Room

def reset_room_status():
    db = SessionLocal()
    try:
        # Find Room 102
        room = db.query(Room).filter(Room.number == "102").first()
        
        if room:
            print(f"Found Room {room.number}")
            print(f"Current Status: {room.status}")
            
            # Reset to Available
            room.status = "Available"
            db.commit()
            
            print(f"✓ Room {room.number} status updated to: {room.status}")
        else:
            print("Room 102 not found")
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_room_status()
