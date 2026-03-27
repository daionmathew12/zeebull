import sys
from app.database import SessionLocal
from app.models.room import Room
from app.models.booking import Booking, BookingRoom
from app.models.checkout import Checkout
from app.models.Package import PackageBooking, PackageBookingRoom

def check_db():
    db = SessionLocal()
    target_rooms = ['103', '001']
    
    with open("check_active_rooms_db_output_utf8.txt", "w", encoding="utf-8") as f:
        f.write("=== Checking Active Rooms Logic ===\n")
        
        for r_num in target_rooms:
            f.write(f"\n--- Room {r_num} ---\n")
            room = db.query(Room).filter(Room.number == r_num).first()
            if not room:
                f.write(f"Room {r_num} not found!\n")
                continue
                
            f.write(f"Room Status: {room.status}\n")
            
            # Check active bookings
            bookings = (db.query(Booking)
                        .join(BookingRoom)
                        .filter(BookingRoom.room_id == room.id)
                        .order_by(Booking.id.desc())
                        .limit(5)
                        .all())
            
            f.write("Recent Bookings:\n")
            for b in bookings:
                f.write(f"  Booking ID: {b.id} | Status: {b.status} | Guest: {b.guest_name} | CheckOut: {b.check_out}\n")
                # Check checkouts
                chk = db.query(Checkout).filter(Checkout.booking_id == b.id).order_by(Checkout.id.desc()).first()
                if chk:
                    f.write(f"    -> Checkout Found: ID {chk.id} | Amount: {chk.grand_total}\n")
                else:
                    f.write(f"    -> No Checkout Record found for this booking\n")
            
            # Check active package bookings
            pkg_bookings = (db.query(PackageBooking)
                            .join(PackageBookingRoom)
                            .filter(PackageBookingRoom.room_id == room.id)
                            .order_by(PackageBooking.id.desc())
                            .limit(5)
                            .all())
                            
            f.write("Recent Package Bookings:\n")
            for pb in pkg_bookings:
                f.write(f"  Pkg Booking ID: {pb.id} | Status: {pb.status} | CheckOut: {pb.check_out}\n")
                chk = db.query(Checkout).filter(Checkout.package_booking_id == pb.id).order_by(Checkout.id.desc()).first()
                if chk:
                    f.write(f"    -> Checkout Found: ID {chk.id} | Amount: {chk.grand_total}\n")
                else:
                    f.write(f"    -> No Checkout Record found for this package booking\n")

    db.close()

if __name__ == "__main__":
    check_db()
