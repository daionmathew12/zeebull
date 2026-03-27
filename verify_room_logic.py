import os
from sqlalchemy import create_engine, text, func, or_
from dotenv import load_dotenv

# Load .env
load_dotenv('ResortApp/.env')
DB_URL = os.getenv('DATABASE_URL')
engine = create_engine(DB_URL)

with engine.connect() as conn:
    print("Checking Room ID 2 (101) status with func.lower()...")
    res = conn.execute(text("SELECT id, number, status FROM rooms WHERE id = 2")).fetchone()
    if res:
        id, number, status = res
        print(f"Room: ID={id}, No={number}, Status='{status}'")
        status_lower = status.lower() if status else ""
        print(f"Lowered Status: '{status_lower}'")
        
        # Check against the conditions in crud/packages.py
        is_checked_in = status_lower == 'checked-in'
        is_occupied = status_lower == 'occupied'
        print(f"Is checked-in? {is_checked_in}")
        print(f"Is occupied? {is_occupied}")
        
        if is_checked_in or is_occupied:
            print("MATCHED! This room IS seen as occupied by the code.")
        else:
            print("NOT MATCHED. The code should NOT think this room is occupied.")
    else:
        print("Room ID 2 not found!")
