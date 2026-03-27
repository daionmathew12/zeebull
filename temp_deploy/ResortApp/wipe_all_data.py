from app.database import SessionLocal
from app.models.checkout import CheckoutPayment, CheckoutVerification, CheckoutRequest, Checkout
from app.models.service_request import ServiceRequest
from app.models.foodorder import FoodOrderItem, FoodOrder
from app.models.Package import PackageBookingRoom, PackageBooking
from app.models.booking import BookingRoom, Booking
from app.models.inventory import (
    StockIssue, StockIssueDetail, InventoryTransaction, LocationStock, Location, 
    InventoryItem, PurchaseDetail, PurchaseMaster, StockRequisition, StockRequisitionDetail,
    WasteLog
)
from sqlalchemy import text

def wipe_all_data():
    db = SessionLocal()
    try:
        print("=== COMMENCING COMPLETE SYSTEM WIPE ===")
        print("(Preserving Master Data: Users, Rooms, Employees, Vendors, Inventory Items, Categories, Locations)")

        # --- 1. GUEST OPERATIONS (Bookings, Checkouts, Services) ---
        print("\n[1/4] Clearing Guest Operations...")
        print("  - Checkout Requests...")
        db.query(CheckoutRequest).delete()
        print("  - Checkout Payments...")
        db.query(CheckoutPayment).delete()
        print("  - Checkout Verifications...")
        db.query(CheckoutVerification).delete()
        print("  - Checkouts...")
        db.query(Checkout).delete()
        
        print("  - Service Requests...")
        db.query(ServiceRequest).delete()
        print("  - Food Order Items...")
        db.query(FoodOrderItem).delete()
        print("  - Food Orders...")
        db.query(FoodOrder).delete()
        
        print("  - Package Booking Rooms...")
        db.query(PackageBookingRoom).delete()
        print("  - Package Bookings...")
        db.query(PackageBooking).delete()
        print("  - Booking Rooms...")
        db.query(BookingRoom).delete()
        print("  - Bookings...")
        db.query(Booking).delete()
        
        print("  - Resetting Room Status to 'Available'...")
        from app.models.room import Room
        db.query(Room).update({Room.status: "Available"}, synchronize_session=False)

        # --- 2. INVENTORY TRANSACTIONS & HISTORY ---
        print("\n[2/4] Clearing Inventory History...")
        print("  - Inventory Transactions (ALL)...")
        db.query(InventoryTransaction).delete()

        print("  - Stock Issue Details...")
        db.query(StockIssueDetail).delete()
        print("  - Stock Issues...")
        db.query(StockIssue).delete()
        
        print("  - Stock Requisition Details...")
        db.query(StockRequisitionDetail).delete()
        print("  - Stock Requisitions...")
        db.query(StockRequisition).delete()

        print("  - Purchase Details...")
        db.query(PurchaseDetail).delete()
        print("  - Purchase Masters...")
        db.query(PurchaseMaster).delete()

        print("  - Waste Logs...")
        db.query(WasteLog).delete()

        # --- 3. STOCK LEVELS ---
        print("\n[3/4] Resetting Stock Levels...")
        print("  - Deleting ALL Location Stock records...")
        db.query(LocationStock).delete()

        print("  - Resetting Global Inventory Item Stock to 0...")
        db.execute(text("UPDATE inventory_items SET current_stock = 0.0"))
        
        # --- 4. COMMIT ---
        db.commit()
        print("\n[4/4] SUCCESS: System Wiped Clean.")

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Wipe Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    wipe_all_data()
