
import os
import sys
from datetime import date, timedelta

# Add the project directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'ResortApp')))

try:
    from app.database import SessionLocal, engine, Base
    from app.api.booking import create_booking, create_guest_booking
    from app.schemas.booking import BookingCreate
    from app.models.room import Room
    from app.models.Package import Package
    from app.models.user import User, Role
    from app.models.branch import Branch
    print("Imports successful")
except Exception as e:
    print(f"Import failed: {e}")
    sys.exit(1)

def test_booking_fix():
    db = SessionLocal()
    try:
        # 1. Setup minimal test data
        # Ensure a branch exists
        branch = db.query(Branch).first()
        if not branch:
            branch = Branch(name="Test Branch", location="Test Loc")
            db.add(branch)
            db.commit()
            db.refresh(branch)
        
        # Ensure a room exists in that branch
        room = db.query(Room).filter(Room.branch_id == branch.id).first()
        if not room:
            room = Room(number="999", type="Test", price=1000, adults=2, children=2, branch_id=branch.id)
            db.add(room)
            db.commit()
            db.refresh(room)
        
        # 2. Test create_guest_booking logic (simulating the call)
        # This will trigger the code I modified
        booking_data = BookingCreate(
            guest_name="Test Guest",
            guest_email="test@example.com",
            guest_mobile="1234567890",
            check_in=date.today(),
            check_out=date.today() + timedelta(days=2),
            adults=1,
            children=0,
            room_ids=[room.id],
            branch_id=branch.id
        )
        
        print(f"Attempting to create guest booking for Room {room.number}...")
        
        # We call the function directly. It uses Depends(get_db) so we pass db manually inside 
        # but the function signature in the code is create_guest_booking(booking: BookingCreate, db: Session = Depends(get_db), ...)
        # FastAPI handles dependencies, but here we call it as a normal function.
        
        try:
            result = create_guest_booking(booking=booking_data, db=db, branch_id_query=branch.id)
            print("Successfully created guest booking!")
            print(f"Booking ID: {result.id}, Display ID: {getattr(result, 'display_id', 'N/A')}")
        except Exception as e:
            print(f"Failed to create guest booking: {e}")
            import traceback
            traceback.print_exc()

    finally:
        db.close()

if __name__ == "__main__":
    test_booking_fix()
