import sys
import os
sys.path.append(os.getcwd())
from sqlalchemy import create_engine, text
from app.database import SQLALCHEMY_DATABASE_URL

def inspect():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    tables = ['rooms', 'packages', 'bookings', 'package_bookings', 'service_requests', 'assigned_services']
    with engine.connect() as conn:
        for table in tables:
            print(f"\n--- {table} ---")
            try:
                res = conn.execute(text(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{table}'"))
                for r in res:
                    print(f"{r[0]}: {r[1]}")
            except Exception as e:
                print(f"Error inspecting {table}: {e}")

if __name__ == "__main__":
    inspect()
