from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.service_request import ServiceRequest
from app.models.foodorder import FoodOrder, FoodOrderItem
from app.models.food_item import FoodItem
from sqlalchemy.orm import joinedload

DATABASE_URL = "postgresql+psycopg2://postgres:qwerty123@localhost:5432/orchiddb"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    print("Attempting to query ServiceRequests with joinedloads...")
    query = db.query(ServiceRequest).options(
        joinedload(ServiceRequest.food_order).joinedload(FoodOrder.items).joinedload(FoodOrderItem.food_item)
    )
    results = query.limit(5).all()
    print(f"Success! Found {len(results)} service requests.")
    for res in results:
        print(f"  SR ID: {res.id}, Type: {res.request_type}")
        if res.food_order:
             print(f"    Food Order ID: {res.food_order.id}")
    
except Exception as e:
    import traceback
    print("FAILED!")
    traceback.print_exc()
finally:
    db.close()
