from app.database import engine
from sqlalchemy import text

def check_columns():
    with engine.connect() as conn:
        print("Checking package_bookings columns...")
        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'package_bookings';"))
        columns = [row[0] for row in result]
        print(f"Columns: {columns}")
        if 'total_amount' in columns:
            print("total_amount EXISTS")
        else:
            print("total_amount MISSING")

if __name__ == "__main__":
    check_columns()
