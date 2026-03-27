from app.database import SessionLocal
from app.api.checkout import _calculate_bill_for_single_room

def test():
    db = SessionLocal()
    res = _calculate_bill_for_single_room(db, "103")
    charges = res["charges"]
    
    print("\n--- INVENTORY USAGE ---")
    for item in charges.inventory_usage:
        print(f"Item: {item['item_name']} | Price: {item['rental_price']} | Charge: {item['rental_charge']} | Note: {item['notes']}")
    
    print(f"\nTOTAL INVENTORY CHARGES: {charges.inventory_charges}")
    
    print("\n--- ASSET DAMAGES ---")
    for dmg in charges.asset_damages:
        print(f"Damage: {dmg['item_name']} | Cost: {dmg['replacement_cost']}")
    
    print(f"\nTOTAL DAMAGE CHARGES: {charges.asset_damage_charges}")
    
    db.close()

if __name__ == "__main__":
    test()
