import sys
import os
sys.path.append(os.getcwd())
import traceback
from app.database import SessionLocal
from app.models.checkout import CheckoutRequest
from app.models.room import Room
from app.models.inventory import LocationStock, AssetRegistry
from app.curd import inventory as inventory_crud

db = SessionLocal()

print("Searching for CheckoutRequests...")
# Find requests for Room 103
reqs = db.query(CheckoutRequest).filter(CheckoutRequest.room_number == '103').all()
print(f"Found {len(reqs)} requests for Room 103")

if not reqs:
    print("No requests for 103 found. Listing all:")
    all_reqs = db.query(CheckoutRequest).limit(5).all()
    for r in all_reqs:
        print(f"  ID: {r.id}, Room: {r.room_number}, Status: {r.status}")
    sys.exit(1)
    
target_req = reqs[-1] # Valid assumption: latest one
print(f"Debugging Latest CheckoutRequest ID: {target_req.id}")

req = target_req
req_id = req.id

# ... same debug logic ...
print(f"Room Number: {req.room_number}")
print(f"Booking ID: {req.booking_id}")
print(f"Package Booking ID: {req.package_booking_id}")

try:
    if req.booking_id:
        print(f"Booking found: {req.booking_id}")
        if req.booking:
             print(f"Booking object loaded. Request ID: {req.booking.id}")
    else:
         print("Booking ID is None")
         # Check package booking
         if req.package_booking_id:
             print(f"Package Booking found: {req.package_booking_id}")
except Exception as e:
    print(f"Error accessing booking: {e}")
    traceback.print_exc()

room = db.query(Room).filter(Room.number == req.room_number).first()
if not room:
    print("Room not found")
    sys.exit(1)
    
loc_id = room.inventory_location_id
print(f"Location ID: {loc_id}")

if not loc_id:
    print("No location ID")
    sys.exit(1)

stocks = db.query(LocationStock).filter(LocationStock.location_id == loc_id, LocationStock.quantity > 0).all()
print(f"Found {len(stocks)} stocks")

for stock in stocks:
    item = stock.item
    if not item:
         print(f"Stock {stock.id}: MISSING ITEM RELATION")
         continue
    print(f"Stock {stock.id}: Item {item.id} - {item.name}, CatID: {item.category_id}")
    try:
        from app.models.inventory import InventoryCategory
        cat = db.query(InventoryCategory).filter(InventoryCategory.id == item.category_id).first()
        print(f"  Category: {cat.name if cat else 'None'}")
    except Exception as e:
        print(f"  Error fetching category: {e}")

assets = db.query(AssetRegistry).filter(AssetRegistry.current_location_id == loc_id).all()
print(f"Found {len(assets)} assets")
for asset in assets:
    print(f"Asset {asset.id}: {asset.item.name}")
