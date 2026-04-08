import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ResortApp')))

from app.database import SessionLocal
from app.api.checkout import _calculate_bill_for_single_room

def test_live_bill():
    db = SessionLocal()
    try:
        print("Calculating bill for Room 101...")
        bill_data = _calculate_bill_for_single_room(db, "101", 1)
        charges = bill_data['charges']
        
        print(f"\n--- BILL SUMMARY ---")
        print(f"Room Charges:       {charges.room_charges}")
        print(f"Inventory Charges:  {charges.inventory_charges}")
        print(f"Consumables:        {charges.consumables_charges}")
        print(f"Asset Damages:      {charges.asset_damage_charges}")
        print(f"Total Due:          {charges.total_due}")
        
        print(f"\n--- RENTAL USAGE ENTRIES ---")
        for u in charges.inventory_usage:
            print(f"  Item: {u['item_name']}, Qty: {u['quantity']}, Price: {u['rental_price']}, Charge: {u['rental_charge']}")
        
        if charges.inventory_charges and charges.inventory_charges > 0:
            print(f"\nSUCCESS: Rental charge {charges.inventory_charges} reflected in bill!")
        else:
            print(f"\nFAILURE: Rental charge is {charges.inventory_charges}")
    finally:
        db.close()

if __name__ == "__main__":
    test_live_bill()
