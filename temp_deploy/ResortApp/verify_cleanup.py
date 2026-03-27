
from app.database import SessionLocal
from sqlalchemy import text

def verify_clear():
    db = SessionLocal()
    try:
        tables = ["bookings", "purchase_masters", "inventory_transactions", "food_orders", "service_requests"]
        print("Verification Results:")
        for table in tables:
            result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.fetchone()[0]
            print(f"  {table}: {count} rows")
            
        result = db.execute(text("SELECT COUNT(*) FROM rooms WHERE status != 'Available'"))
        non_available = result.fetchone()[0]
        print(f"  Rooms NOT available: {non_available}")
        
    finally:
        db.close()

if __name__ == "__main__":
    verify_clear()
