
from app.database import SessionLocal
from app.models.room import Room
from app.models.booking import Booking, BookingRoom
from app.models.Package import PackageBookingRoom, PackageBooking
from app.models.inventory import LocationStock, AssetMapping, AssetRegistry, Location
from app.models.checkout import CheckoutRequest

db = SessionLocal()

room_number = "001"
room = db.query(Room).filter(Room.number == room_number).first()
if not room:
    print(f"Room {room_number} NOT FOUND")
else:
    print(f"Room {room_number}: ID={room.id}, LocID={room.inventory_location_id}")
    if room.inventory_location_id:
        loc = db.query(Location).filter(Location.id == room.inventory_location_id).first()
        if loc:
            print(f"Location: ID={loc.id}, Name={loc.name}")
        else:
            print(f"Location ID {room.inventory_location_id} NOT FOUND")
        
        stocks = db.query(LocationStock).filter(LocationStock.location_id == room.inventory_location_id).all()
        print(f"LocationStocks count for loc {room.inventory_location_id}: {len(stocks)}")
        for s in stocks:
            print(f"  Item ID {s.item_id}: Qty {s.quantity}")
            
        mappings = db.query(AssetMapping).filter(AssetMapping.location_id == room.inventory_location_id, AssetMapping.is_active == True).all()
        print(f"AssetMappings count: {len(mappings)}")
        
        registry = db.query(AssetRegistry).filter(AssetRegistry.current_location_id == room.inventory_location_id).all()
        print(f"AssetRegistry count: {len(registry)}")
    else:
        print("Room HAS NO inventory_location_id")

reqs = db.query(CheckoutRequest).filter(CheckoutRequest.room_number == room_number).order_by(CheckoutRequest.id.desc()).all()
print(f"CheckoutRequests for {room_number}: {len(reqs)}")
for r in reqs:
    print(f"  ID {r.id}: Status={r.status}, BookingID={r.booking_id}, PackageBookingID={r.package_booking_id}")

db.close()
