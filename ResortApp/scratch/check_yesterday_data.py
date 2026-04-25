
import sys
import os
from datetime import date, datetime, timedelta

# Add current directory to path so we can import app
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.booking import Booking, BookingRoom
from app.models.Package import PackageBooking, PackageBookingRoom
from app.models.checkout import Checkout
from app.models.foodorder import FoodOrder
from app.models.service_request import ServiceRequest
from app.models.payment import Payment
from app.models.room import Room

def check_yesterday():
    db = SessionLocal()
    yesterday = date(2026, 4, 22)
    print(f"--- Checking data for {yesterday} ---")
    
    try:
        # 1. Room Bookings arriving, departing or in-house yesterday
        print("\n[ROOM BOOKINGS]")
        bookings = db.query(Booking).filter(
            (Booking.check_in <= yesterday) & (Booking.check_out >= yesterday)
        ).all()
        if not bookings:
            print("No room bookings found for yesterday.")
        for b in bookings:
            print(f"ID: {b.id}, Guest: {b.guest_name}, Check-in: {b.check_in}, Check-out: {b.check_out}, Status: {b.status}")
            if b.status == "checked_in":
                 print(f"  - Checked in at: {b.checked_in_at}")
            elif b.status == "checked_out":
                 print(f"  - Checked out at: {b.checked_out_at}")

        # 2. Package Bookings
        print("\n[PACKAGE BOOKINGS]")
        p_bookings = db.query(PackageBooking).filter(
            (PackageBooking.check_in <= yesterday) & (PackageBooking.check_out >= yesterday)
        ).all()
        if not p_bookings:
            print("No package bookings found for yesterday.")
        for b in p_bookings:
            print(f"ID: {b.id}, Guest: {b.guest_name}, Check-in: {b.check_in}, Check-out: {b.check_out}, Status: {b.status}")

        # 3. Checkouts yesterday
        print("\n[CHECKOUTS]")
        checkouts = db.query(Checkout).all()
        yesterday_checkouts = [c for c in checkouts if c.checkout_date and c.checkout_date.date() == yesterday]
        if not yesterday_checkouts:
            print("No checkouts recorded for yesterday.")
        for c in yesterday_checkouts:
            print(f"ID: {c.id}, Booking ID: {c.booking_id}, Total: {c.grand_total}, Status: {c.payment_status}")

        # 4. Food Orders yesterday
        print("\n[FOOD ORDERS]")
        food_orders = db.query(FoodOrder).all()
        yesterday_orders = [o for o in food_orders if o.created_at and o.created_at.date() == yesterday]
        if not yesterday_orders:
            print("No food orders found for yesterday.")
        for o in yesterday_orders:
            total = o.total_with_gst if o.total_with_gst is not None else o.amount
            print(f"ID: {o.id}, Room: {o.room_id}, Total: {total}, Status: {o.status}")

        # 5. Service Requests yesterday
        print("\n[SERVICE REQUESTS]")
        service_requests = db.query(ServiceRequest).all()
        yesterday_sr = [sr for sr in service_requests if sr.created_at and sr.created_at.date() == yesterday]
        if not yesterday_sr:
            print("No service requests found for yesterday.")
        for sr in yesterday_sr:
            print(f"ID: {sr.id}, Room: {sr.room_id}, Type: {sr.request_type}, Status: {sr.status}")

        # 6. Payments yesterday
        print("\n[PAYMENTS]")
        payments = db.query(Payment).all()
        yesterday_payments = [p for p in payments if p.payment_date and p.payment_date.date() == yesterday]
        if not yesterday_payments:
            print("No payments found for yesterday.")
        for p in yesterday_payments:
            print(f"ID: {p.id}, Amount: {p.amount}, Method: {p.payment_method}, Status: {p.status}")

    finally:
        db.close()

if __name__ == "__main__":
    check_yesterday()
