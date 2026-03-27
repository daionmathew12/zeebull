from app.api.report import get_user_history
from app.database import SessionLocal
from datetime import date

def test_api():
    db = SessionLocal()
    # Mock current_user
    current_user = {"id": 30} # kk's user id
    
    # Test for today
    today = date(2026, 1, 23)
    res = get_user_history(user_id=30, from_date=today, to_date=today, db=db, current_user=current_user)
    
    print(f"User: {res.user_name}")
    print(f"Activities found: {len(res.activities)}")
    for act in res.activities:
        print(f"[{act.type}] {act.activity_date}: {act.description}")

if __name__ == "__main__":
    test_api()
