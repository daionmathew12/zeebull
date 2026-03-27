from app.database import SessionLocal
from app.models.booking import Booking, BookingRoom
from app.models.room import Room
from app.models.inventory import LocationStock, StockIssue, StockIssueDetail

db = SessionLocal()

print("=== DIAGNOSING BLANK ALLOCATION DISPLAY ===")

# 1. Get Latest Booking
latest_booking = db.query(Booking).order_by(Booking.id.desc()).first()
if not latest_booking:
    print("❌ No bookings found!")
    exit()

print(f"\n[1] Latest Booking: {latest_booking.id} (Guest: {latest_booking.guest_name})")

# 2. Get Rooms for this Booking
booking_rooms = db.query(BookingRoom).filter(BookingRoom.booking_id == latest_booking.id).all()
if not booking_rooms:
    print("❌ No rooms linked to this booking!")
else:
    for br in booking_rooms:
        room = db.query(Room).filter(Room.id == br.room_id).first()
        print(f"   - Room # {room.number} (ID: {room.id}) Status: '{room.status}'")
        print(f"     Inventory Location ID: {room.inventory_location_id}")
        
        if not room.inventory_location_id:
             print("     ⚠️ WARNING: Room has no Inventory Location ID! Allocation impossible.")
             continue

        # 3. Check Location Stock for this Room
        stocks = db.query(LocationStock).filter(LocationStock.location_id == room.inventory_location_id).all()
        print(f"     [Stock Check in Location {room.inventory_location_id}]:")
        if not stocks:
            print("       ❌ EMPTY. No items found in LocationStock table for this room.")
        else:
            for s in stocks:
                item_name = s.item.name if s.item else "Unknown"
                print(f"       ✅ Found: {item_name} (Qty: {s.quantity})")

        # 4. Check Stock Issues (Allocations) targeting this Location
        issues = db.query(StockIssue).filter(StockIssue.destination_location_id == room.inventory_location_id).all()
        print(f"     [Allocation History for Location {room.inventory_location_id}]:")
        if not issues:
            print("       ❌ No Stock Issue records found targeting this location.")
        else:
            for i in issues:
                print(f"       ✅ Issue #{i.issue_number} (Source: {i.source_location_id})")
                details = db.query(StockIssueDetail).filter(StockIssueDetail.issue_id == i.id).all()
                for d in details:
                    item_name = d.item.name if d.item else "Unknown"
                    print(f"          - Allocated: {item_name} (Qty: {d.issued_quantity})")

db.close()
