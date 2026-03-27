from app.database import SessionLocal
from app.models.inventory import LocationStock, AssetMapping

def check_stock():
    db = SessionLocal()
    loc_id = 6 # Room 103 Loc ID
    
    for iid in [4, 22, 6]: # TV, Bulb, Towel
        ls = db.query(LocationStock).filter(LocationStock.location_id == loc_id, LocationStock.item_id == iid).first()
        am = db.query(AssetMapping).filter(AssetMapping.location_id == loc_id, AssetMapping.item_id == iid, AssetMapping.is_active == True).first()
        
        ls_q = ls.quantity if ls else 0
        am_q = am.quantity if am else 0
        
        print(f"ID:{iid} | ls:{ls_q} | am:{am_q}")
    db.close()

if __name__ == "__main__":
    check_stock()
