"""Quick diagnostic: check what data exists for room 101 in DB."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("PYTHONPATH", ".")

from app.database import SessionLocal
from app.models.room import Room
from app.models.booking import Booking, BookingRoom
from app.models.service_request import ServiceRequest
from app.models.inventory import InventoryTransaction

db = SessionLocal()

# Find the room
room = db.query(Room).filter(Room.number == "101").first()
if not room:
    room = db.query(Room).first()
    print(f"Room 101 not found, using first room: {room.number if room else 'NONE'}")
else:
    print(f"Found Room 101: ID={room.id}, status={room.status}, inventory_location_id={room.inventory_location_id}")

if room:
    # Check bookings via BookingRoom join
    booking_rooms = db.query(BookingRoom).filter(BookingRoom.room_id == room.id).all()
    print(f"\nBookingRoom records for room {room.id}: {len(booking_rooms)}")
    for br in booking_rooms:
        b = db.query(Booking).filter(Booking.id == br.booking_id).first()
        if b:
            print(f"  Booking ID={b.id}, guest={b.guest_name}, status={b.status}, check_in={b.check_in}")

    # Check service requests
    try:
        srs = db.query(ServiceRequest).filter(ServiceRequest.room_id == room.id).all()
        print(f"\nServiceRequests for room {room.id}: {len(srs)}")
        for sr in srs:
            print(f"  SR ID={sr.id}, type={sr.request_type}, status={sr.status}")
    except Exception as e:
        print(f"ServiceRequest error: {e}")

    # Check inventory transactions
    if room.inventory_location_id:
        from sqlalchemy import or_
        txns = db.query(InventoryTransaction).filter(
            or_(
                InventoryTransaction.source_location_id == room.inventory_location_id,
                InventoryTransaction.destination_location_id == room.inventory_location_id
            )
        ).all()
        print(f"\nInventoryTransactions for location {room.inventory_location_id}: {len(txns)}")
    else:
        print(f"\nRoom has NO inventory_location_id set!")

db.close()
