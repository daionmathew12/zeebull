#!/usr/bin/env python3
"""
Clear all transactional data (bookings, services, checkouts, etc.)
Keeps master data (users, rooms, inventory items, service definitions, etc.)
"""

from app.database import SessionLocal
from app.models.booking import Booking, BookingRoom
from app.models.Package import PackageBooking, PackageBookingRoom
from app.models.service import AssignedService
from app.models.employee_inventory import EmployeeInventoryAssignment
from app.models.service_request import ServiceRequest
from app.models.checkout import Checkout, CheckoutRequest, CheckoutPayment, CheckoutVerification
from app.models.foodorder import FoodOrder, FoodOrderItem
from app.models.inventory import (
    InventoryTransaction, LocationStock, StockIssue, StockIssueDetail,
    PurchaseMaster, PurchaseDetail, WasteLog, AssetRegistry, AssetMapping, LaundryLog
)
from app.models.notification import Notification

db = SessionLocal()

print("🧹 Clearing all transactional data...")
print("=" * 60)

# Track counts
counts = {}

# 1. Checkouts (must be deleted before bookings due to FK)
print("\n💳 Clearing checkouts...")
print("\n💳 Clearing checkouts...")
counts['checkout_payments'] = db.query(CheckoutPayment).count()
counts['checkout_verifications'] = db.query(CheckoutVerification).count()
counts['checkout_requests'] = db.query(CheckoutRequest).count()
counts['checkouts'] = db.query(Checkout).count()

db.query(CheckoutPayment).delete()
db.query(CheckoutVerification).delete()
db.query(CheckoutRequest).delete()
db.query(Checkout).delete()

print(f"   ✅ Deleted {counts['checkouts']} checkouts")
print(f"   ✅ Deleted {counts['checkout_verifications']} checkout verifications")
print(f"   ✅ Deleted {counts['checkout_requests']} checkout requests")
print(f"   ✅ Deleted {counts['checkout_payments']} checkout payments")

# 2. Service Requests
print("\n📋 Clearing service requests...")
counts['service_requests'] = db.query(ServiceRequest).count()
db.query(ServiceRequest).delete()
print(f"   ✅ Deleted {counts['service_requests']} service requests")

# 3. Food Orders
print("\n🍽️  Clearing food orders...")
counts['food_order_items'] = db.query(FoodOrderItem).count()
counts['food_orders'] = db.query(FoodOrder).count()

db.query(FoodOrderItem).delete()
db.query(FoodOrder).delete()

print(f"   ✅ Deleted {counts['food_order_items']} food order items")
print(f"   ✅ Deleted {counts['food_orders']} food orders")

# 4. Services
print("\n🛎️  Clearing assigned services...")
counts['employee_inventory_assignments'] = db.query(EmployeeInventoryAssignment).count()
counts['assigned_services'] = db.query(AssignedService).count()

db.query(EmployeeInventoryAssignment).delete()
db.query(AssignedService).delete()

print(f"   ✅ Deleted {counts['employee_inventory_assignments']} employee inventory assignments")
print(f"   ✅ Deleted {counts['assigned_services']} assigned services")

# 5. Bookings (after checkouts are deleted)
print("\n📅 Clearing bookings...")
counts['bookings'] = db.query(Booking).count()
counts['booking_rooms'] = db.query(BookingRoom).count()
counts['package_bookings'] = db.query(PackageBooking).count()
counts['package_booking_rooms'] = db.query(PackageBookingRoom).count()

db.query(BookingRoom).delete()
db.query(Booking).delete()
db.query(PackageBookingRoom).delete()
db.query(PackageBooking).delete()

print(f"   ✅ Deleted {counts['bookings']} bookings")
print(f"   ✅ Deleted {counts['booking_rooms']} booking rooms")
print(f"   ✅ Deleted {counts['package_bookings']} package bookings")
print(f"   ✅ Deleted {counts['package_booking_rooms']} package booking rooms")

# 6. Inventory Transactions
print("\n📦 Clearing inventory transactions...")
counts['transactions'] = db.query(InventoryTransaction).count()
counts['location_stocks'] = db.query(LocationStock).count()
counts['stock_issue_details'] = db.query(StockIssueDetail).count()
counts['stock_issues'] = db.query(StockIssue).count()
counts['purchase_details'] = db.query(PurchaseDetail).count()
counts['purchases'] = db.query(PurchaseMaster).count()
counts['waste_logs'] = db.query(WasteLog).count()
counts['laundry_logs'] = db.query(LaundryLog).count()

db.query(InventoryTransaction).delete()
db.query(LocationStock).delete()
db.query(StockIssueDetail).delete()
db.query(StockIssue).delete()
db.query(PurchaseDetail).delete()
db.query(PurchaseMaster).delete()
db.query(WasteLog).delete()
db.query(LaundryLog).delete()

print(f"   ✅ Deleted {counts['transactions']} transactions")
print(f"   ✅ Deleted {counts['location_stocks']} location stocks")
print(f"   ✅ Deleted {counts['stock_issue_details']} stock issue details")
print(f"   ✅ Deleted {counts['stock_issues']} stock issues")
print(f"   ✅ Deleted {counts['purchase_details']} purchase details")
print(f"   ✅ Deleted {counts['purchases']} purchases")
print(f"   ✅ Deleted {counts['waste_logs']} waste logs")
print(f"   ✅ Deleted {counts['laundry_logs']} laundry logs")

# 7. Assets and Mappings
print("\n🏢 Clearing asset registries and mappings...")
counts['asset_registry'] = db.query(AssetRegistry).count()
counts['asset_mappings'] = db.query(AssetMapping).count()

db.query(AssetRegistry).delete()
db.query(AssetMapping).delete()

print(f"   ✅ Deleted {counts['asset_registry']} asset registry entries")
print(f"   ✅ Deleted {counts['asset_mappings']} asset mappings")

# 7. Reset item stocks to 0
print("\n🔄 Resetting item stocks...")
from app.models.inventory import InventoryItem
items = db.query(InventoryItem).all()
reset_count = 0
for item in items:
    if item.current_stock != 0:
        item.current_stock = 0
        reset_count += 1
print(f"   ✅ Reset {reset_count} items to 0 stock")

# 8. Notifications
print("\n🔔 Clearing notifications...")
counts['notifications'] = db.query(Notification).count()
db.query(Notification).delete()
print(f"   ✅ Deleted {counts['notifications']} notifications")

# 9. Reset room statuses to Available
print("\n🏨 Resetting room statuses...")
from app.models.room import Room
rooms = db.query(Room).all()
reset_rooms = 0
for room in rooms:
    if room.status != "Available":
        room.status = "Available"
        reset_rooms += 1
print(f"   ✅ Reset {reset_rooms} rooms to Available")

db.commit()

print("\n" + "=" * 60)
print("✅ All transactional data cleared!")
print("\n📊 Summary:")
total = sum(counts.values()) + reset_count + reset_rooms
print(f"   Total records deleted/reset: {total}")

print("\n✅ Master data preserved:")
print("   - Users & Employees")
print("   - Rooms & Room Types")
print("   - Inventory Items & Categories")
print("   - Service Definitions")
print("   - Vendors & Suppliers")
print("   - Locations")

print("\n🎉 System is now ready for fresh data!")

db.close()
