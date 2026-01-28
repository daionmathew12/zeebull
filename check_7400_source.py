import sys
sys.path.insert(0, '/var/www/inventory/ResortApp')

from app.database import SessionLocal
from app.models.booking import Booking
from app.models.checkout import Checkout
from datetime import date, timedelta

db = SessionLocal()

today = date.today()
print(f"Today's date: {today}")

# Check bookings for today
print("\n=== BOOKINGS FOR TODAY ===")
today_bookings = db.query(Booking).filter(
    Booking.check_in <= today,
    Booking.check_out >= today
).all()

print(f"Total bookings active today: {len(today_bookings)}")
total_booking_amount = 0
for b in today_bookings:
    print(f"  Booking #{b.id}: {b.guest_name}, Check-in: {b.check_in}, Check-out: {b.check_out}, Amount: ₹{b.total_amount}")
    total_booking_amount += (b.total_amount or 0)

print(f"\nTotal booking amount: ₹{total_booking_amount}")

# Check checkouts for today
print("\n=== CHECKOUTS FOR TODAY ===")
today_checkouts = db.query(Checkout).filter(
    Checkout.checkout_date == today
).all()

print(f"Total checkouts today: {len(today_checkouts)}")
total_checkout_amount = 0
for c in today_checkouts:
    print(f"  Checkout #{c.id}: Date: {c.checkout_date}, Grand Total: ₹{c.grand_total}")
    total_checkout_amount += (c.grand_total or 0)

print(f"\nTotal checkout amount: ₹{total_checkout_amount}")

# Check all bookings with total_amount = 7400
print("\n=== BOOKINGS WITH AMOUNT = 7400 ===")
bookings_7400 = db.query(Booking).filter(Booking.total_amount == 7400).all()
print(f"Found {len(bookings_7400)} bookings with amount 7400")
for b in bookings_7400:
    print(f"  Booking #{b.id}: {b.guest_name}, Check-in: {b.check_in}, Check-out: {b.check_out}, Status: {b.status}")

db.close()
