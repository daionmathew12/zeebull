from app.database import SessionLocal
from app.api.checkout import _calculate_bill_for_single_room

def test():
    db = SessionLocal()
    res = _calculate_bill_for_single_room(db, "103")
    print(f"RES_TYPE: {type(res)}")
    if isinstance(res, dict):
        print(f"KEYS: {list(res.keys())}")
    else:
        print(f"DIR: {dir(res)}")
    db.close()

if __name__ == "__main__":
    test()
