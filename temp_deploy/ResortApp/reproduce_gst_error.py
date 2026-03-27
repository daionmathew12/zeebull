
import sys
import os
from datetime import datetime
from fastapi.encoders import jsonable_encoder

# Add the project directory to sys.path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.api.gst_reports import get_itc_register, get_room_tariff_slab_report
from sqlalchemy.orm import Session

# Mock user
class MockUser:
    id = 1
    role = "admin"

def test_itc_register():
    print("\nTesting ITC Register...")
    db = SessionLocal()
    try:
        # Call the function
        result = get_itc_register(
            start_date="2024-01-01",
            end_date="2025-12-31",
            db=db,
            current_user=MockUser()
        )
        print("ITC Register Success! (Logic)")
        encoded = jsonable_encoder(result)
        print("ITC Register Success! (Serialization)")
        # print(result)
    except Exception as e:
        print(f"ITC Register Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def test_room_tariff_slab():
    print("\nTesting Room Tariff Slab...")
    db = SessionLocal()
    try:
        # Call the function
        result = get_room_tariff_slab_report(
            start_date="2024-01-01",
            end_date="2025-12-31",
            db=db,
            current_user=MockUser()
        )
        print("Room Tariff Slab Success! (Logic)")
        encoded = jsonable_encoder(result)
        print("Room Tariff Slab Success! (Serialization)")
        # print(result)
    except Exception as e:
        print(f"Room Tariff Slab Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_itc_register()
    test_room_tariff_slab()
