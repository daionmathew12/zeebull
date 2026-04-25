from app.database import SessionLocal
from app.models.foodorder import FoodOrder
from app.models.room import Room

db = SessionLocal()
room_101 = db.query(Room).filter(Room.number == "101").first()
print(f"Room 101 ID: {room_101.id}")

orders = db.query(FoodOrder).filter(FoodOrder.room_id == room_101.id).all()
print(f"Food Orders for Room 101: {len(orders)}")
for o in orders:
    print(f"  - Order ID: {o.id}, Status: {o.status}, Amount: {o.amount}, Linked SR: {o.service_request.id if getattr(o, 'service_request', None) else 'None'}")
