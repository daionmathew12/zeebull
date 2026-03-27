from app.database import SessionLocal
from app.models.checkout import CheckoutPayment, CheckoutVerification, CheckoutRequest, Checkout
from app.models.service_request import ServiceRequest
from app.models.foodorder import FoodOrderItem, FoodOrder
from app.models.Package import PackageBookingRoom, PackageBooking
from app.models.booking import BookingRoom, Booking
from app.models.inventory import StockIssue, StockIssueDetail, InventoryTransaction, LocationStock, Location
from sqlalchemy import text

def delete_all_bookings():
    db = SessionLocal()
    try:
        print("Starting Comprehensive System Cleanup...")

        # 1. Checkout Related (Child records of Checkout/Booking)
        print("Deleting Checkout Requests...")
        db.query(CheckoutRequest).delete()
        
        print("Deleting Checkout Payments...")
        db.query(CheckoutPayment).delete()
        
        print("Deleting Checkout Verifications...")
        db.query(CheckoutVerification).delete()
        
        print("Deleting Checkouts...")
        db.query(Checkout).delete()

        # 2. Service & Food Orders (Transactional history linked to stay)
        print("Deleting Service Requests...")
        db.query(ServiceRequest).delete()
        
        print("Deleting Food Order Items...")
        db.query(FoodOrderItem).delete()
        
        print("Deleting Food Orders...")
        db.query(FoodOrder).delete()

        # 3. Inventory Allocations & Stock Issues (Allocated Items in Room)
        print("Deleting Stock Issue Details...")
        db.query(StockIssueDetail).delete()
        
        print("Deleting Stock Issues...")
        db.query(StockIssue).delete()

        # Delete Inventory Transactions (Except purchases, maybe? User said 'allocated items', usually implies wiping all movement history)
        # To be safe and thorough as requested ("clear... allocated items"), we wipe transactions related to issues/transfers.
        print("Deleting Inventory Transactions (Issues/Transfers)...")
        db.query(InventoryTransaction).filter(InventoryTransaction.transaction_type.in_(['issue', 'transfer_in', 'transfer_out', 'out', 'in'])).delete(synchronize_session=False)

        # Clear Room Stock (LocationStock for Guest Rooms)
        print("Clearing Allocated Items in Rooms (Location Stock)...")
        # Identify Guest Room Locations
        guest_room_ids = [l.id for l in db.query(Location.id).filter(Location.location_type == 'GUEST_ROOM').all()]
        if guest_room_ids:
             db.query(LocationStock).filter(LocationStock.location_id.in_(guest_room_ids)).delete(synchronize_session=False)

        # 4. Package Bookings
        print("Deleting Package Booking Rooms...")
        db.query(PackageBookingRoom).delete()
        
        print("Deleting Package Bookings...")
        db.query(PackageBooking).delete()

        # 5. Regular Bookings
        print("Deleting Booking Rooms...")
        db.query(BookingRoom).delete()
        
        print("Deleting Bookings...")
        db.query(Booking).delete()

        db.commit()
        print("Successfully cleared all booking, service, and allocation history.")

    except Exception as e:
        db.rollback()
        print(f"Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    delete_all_bookings()
