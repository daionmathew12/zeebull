from app.database import SessionLocal
from app.api.checkout import _calculate_bill_for_single_room
import json

def test_bill():
    db = SessionLocal()
    room_number = "103"
    res = _calculate_bill_for_single_room(db, room_number)
    
    with open("/home/basilabrahamaby/bill_final_report.txt", "w") as f:
        f.write("--- USAGE ---\n")
        for item in res.get('inventory_usage', []):
            f.write(f"{item['item_name']} | Qty:{item['quantity']} | Rent:{item['rental_charge']} | Notes:{item['notes']}\n")
        
        f.write("\n--- DAMAGES ---\n")
        for dmg in res.get('asset_damages', []):
            f.write(f"{dmg['item_name']} | Cost:{dmg['replacement_cost']}\n")
            
    db.close()

if __name__ == "__main__":
    test_bill()
