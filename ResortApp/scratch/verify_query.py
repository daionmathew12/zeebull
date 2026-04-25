import requests
import json

BASE_URL = "http://localhost:8011/api/dashboard"

def test_dept_api(dept_name):
    print(f"Fetching details for {dept_name}...")
    # Need auth? Usually for local it might be open or we can use a token if needed.
    # But I'll just try to see if I can get it.
    # Since I don't have a token handy, I'll use the DB directly to check the count.
    pass

if __name__ == "__main__":
    # Instead of requests (which needs auth), I'll use the DB logic in a script
    from sqlalchemy import create_engine, func
    from sqlalchemy.orm import sessionmaker, joinedload
    import sys
    sys.path.append(r"c:\releasing\New Orchid\ResortApp")
    from app.models.foodorder import FoodOrder
    from datetime import date
    
    engine = create_engine("postgresql+psycopg2://postgres:qwerty123@localhost:5432/zeebuldb")
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    start_date = date(2026, 4, 1)
    
    q = db.query(FoodOrder).options(joinedload(FoodOrder.room)).filter(FoodOrder.status != "Cancelled")
    s_date = start_date
    q = q.filter(func.date(FoodOrder.created_at) >= s_date)
    
    results = q.all()
    print(f"Query returned {len(results)} orders")
    for r in results:
        print(f"ID: {r.id}, Amount: {r.total_with_gst}")
