import sys
import os
from sqlalchemy import text

sys.path.append(os.getcwd())
try:
    from app.database import SessionLocal
    from app.models.inventory import LocationStock
except ImportError:
    sys.path.append(os.path.join(os.getcwd(), 'ResortApp'))
    from app.database import SessionLocal
    from app.models.inventory import LocationStock

def test_raw():
    db = SessionLocal()
    try:
        print("--- Raw SQL Update Test ---")
        ls = db.query(LocationStock).filter(LocationStock.id==75).first()
        if not ls: print("LS 75 not found"); return
        before = ls.quantity
        print(f"Before: {before}")
        
        print("Executing Raw Update (+5)...")
        db.execute(text("UPDATE location_stocks SET quantity = quantity + 5 WHERE id = 75"))
        db.commit()
        
        db.expire_all()
        ls = db.query(LocationStock).filter(LocationStock.id==75).first()
        print(f"After: {ls.quantity}")
        
        if ls.quantity == before + 5:
            print("SUCCESS")
        else:
            print("FAILURE")
    except Exception as e:
        import traceback; traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_raw()
