from app.database import SessionLocal
from app.models.food_category import FoodCategory

db = SessionLocal()
try:
    cats = db.query(FoodCategory).all()
    print(f"Found {len(cats)} categories")
    for cat in cats:
        print(f"ID: {cat.id}, Name: {cat.name}")
finally:
    db.close()
