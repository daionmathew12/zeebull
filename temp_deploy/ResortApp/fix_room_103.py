from app.database import SessionLocal
from app.models.room import Room
from app.models.inventory import InventoryItem, AssetMapping, StockIssue, StockIssueDetail, AssetRegistry
from sqlalchemy import or_

def fix_room_103_data():
    db = SessionLocal()
    room = db.query(Room).filter(Room.number == '103').first()
    if not room:
        print("Room 103 not found")
        return
    
    loc_id = room.inventory_location_id
    print(f"Fixing data for Room 103 (LocID: {loc_id})")

    # 1. LED Bulb (ID: 3)
    # Move damage from Mapping to Rented Issue
    mapping_led = db.query(AssetMapping).filter(AssetMapping.location_id == loc_id, AssetMapping.item_id == 3).first()
    if mapping_led and mapping_led.notes and "Reported Damaged" in mapping_led.notes:
        print("Removing damage note from LED Bulb mapping")
        mapping_led.notes = mapping_led.notes.replace("[Reported Damaged at Checkout #6]", "").strip()
        if not mapping_led.notes: mapping_led.notes = None
    
    rented_issue_led = db.query(StockIssueDetail).join(StockIssue).filter(
        StockIssue.destination_location_id == loc_id,
        StockIssueDetail.item_id == 3,
        or_(StockIssueDetail.rental_price > 0, StockIssueDetail.is_payable == True)
    ).first()
    if rented_issue_led:
        print("Marking Rented LED Bulb issue as DAMAGED")
        rented_issue_led.is_damaged = True
        rented_issue_led.damage_notes = "Reported at Checkout #6 (Corrected)"
    
    # 2. Smart TV (ID: 4)
    # The user said the damaged one was Smart TV, and undamaged was Rented? 
    # Wait: "there was also a damaged smart tv ,the undamaged one was rented smart tv"
    # This implies:
    # - Fixed Asset Smart TV: DAMAGED
    # - Rented Smart TV: UNDAMAGED
    # My previous script showed Smart TV mapping had notes: None.
    # I should mark the Fixed Asset Smart TV mapping as damaged if it wasn't.
    
    mapping_tv = db.query(AssetMapping).filter(AssetMapping.location_id == loc_id, AssetMapping.item_id == 4).first()
    if mapping_tv:
        print("Marking Fixed Asset Smart TV mapping as DAMAGED")
        note = " [Reported Damaged at Checkout #6]"
        if not mapping_tv.notes or note not in mapping_tv.notes:
            mapping_tv.notes = (mapping_tv.notes or "") + note
            
    # Also update AssetRegistry for the TV
    registry_tv = db.query(AssetRegistry).filter(AssetRegistry.item_id == 4, AssetRegistry.current_location_id == loc_id).first()
    if registry_tv:
        print("Updating TV status in Registry to damaged")
        registry_tv.status = "damaged"

    db.commit()
    print("Room 103 data fixed.")
    db.close()

if __name__ == "__main__":
    fix_room_103_data()
