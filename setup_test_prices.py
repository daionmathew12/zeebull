from app.database import SessionLocal
from app.models.room import RoomType
from app.models.calendar import PricingCalendar
from datetime import date
db = SessionLocal()
# 1. Add Holiday
h = PricingCalendar(start_date=date(2026, 5, 10), end_date=date(2026, 5, 12), day_type='HOLIDAY', description='Test Holiday')
db.add(h)
# 2. Set Prices for Room 3
rt = db.query(RoomType).filter(RoomType.id == 3).first()
if rt:
    rt.holiday_price = 5000.0
    rt.weekend_price = 3500.0
    rt.long_weekend_price = 4000.0
db.commit()
print("Test data setup complete")
