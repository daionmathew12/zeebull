import sys
import os
from sqlalchemy import text

sys.path.append(os.getcwd())
try:
    from app.database import SessionLocal
except ImportError:
    sys.path.append(os.path.join(os.getcwd(), 'ResortApp'))
    from app.database import SessionLocal

def fix():
    db = SessionLocal()
    try:
        print("Manually fixing LS 74 to 50.0...")
        db.execute(text("UPDATE location_stocks SET quantity = 50.0 WHERE id = 74"))
        db.commit()
        print("Done.")
    finally:
        db.close()

if __name__ == "__main__":
    fix()
