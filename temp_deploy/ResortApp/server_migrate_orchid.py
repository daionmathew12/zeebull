import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

from app.database import engine, SessionLocal
from sqlalchemy import text
from app.models.foodorder import FoodOrder
from app.models.service import AssignedService
from app.models.booking import Booking, BookingRoom
from app.models.Package import PackageBooking, PackageBookingRoom

def migrate():
    # 1. Add columns
    with engine.connect() as conn:
        print("Ensuring columns exist...")
        try:
            conn.execute(text("ALTER TABLE food_orders ADD COLUMN IF NOT EXISTS booking_id INTEGER REFERENCES bookings(id)"))
            conn.execute(text("ALTER TABLE food_orders ADD COLUMN IF NOT EXISTS package_booking_id INTEGER REFERENCES package_bookings(id)"))
            conn.execute(text("ALTER TABLE assigned_services ADD COLUMN IF NOT EXISTS booking_id INTEGER REFERENCES bookings(id)"))
            conn.execute(text("ALTER TABLE assigned_services ADD COLUMN IF NOT EXISTS package_booking_id INTEGER REFERENCES package_bookings(id)"))
            
            # Stock Issues
            conn.execute(text("ALTER TABLE stock_issues ADD COLUMN IF NOT EXISTS booking_id INTEGER"))
            conn.execute(text("ALTER TABLE stock_issues ADD COLUMN IF NOT EXISTS guest_id INTEGER"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_stock_issues_booking_id ON stock_issues (booking_id)"))
            
            # Stock Issue Details (Manual Damage Mark)
            conn.execute(text("ALTER TABLE stock_issue_details ADD COLUMN IF NOT EXISTS is_damaged BOOLEAN DEFAULT FALSE"))
            conn.execute(text("ALTER TABLE stock_issue_details ADD COLUMN IF NOT EXISTS damage_notes TEXT"))

            # Bookings (Display ID)
            conn.execute(text("ALTER TABLE bookings ADD COLUMN IF NOT EXISTS display_id VARCHAR"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_bookings_display_id ON bookings (display_id)"))
            
            conn.commit()
            print("Columns verified/added.")
        except Exception as e:
            print(f"Error adding columns: {e}")

    # 2. Migrate data
    db = SessionLocal()
    try:
        # Food Orders
        orders = db.query(FoodOrder).filter(FoodOrder.booking_id == None, FoodOrder.package_booking_id == None).all()
        print(f"Found {len(orders)} food orders to migrate.")
        for order in orders:
            ref_dt = order.created_at
            if not ref_dt: continue
            ref_date = ref_dt.date()
            
            # Match regular booking
            booking = db.query(Booking).join(BookingRoom).filter(
                BookingRoom.room_id == order.room_id,
                Booking.check_in <= ref_date,
                Booking.check_out >= ref_date,
                Booking.status != "cancelled"
            ).order_by(Booking.id.desc()).first()
            
            if booking:
                order.booking_id = booking.id
                continue
            
            # Match package booking
            pkg_booking = db.query(PackageBooking).join(PackageBookingRoom).filter(
                PackageBookingRoom.room_id == order.room_id,
                PackageBooking.check_in <= ref_date,
                PackageBooking.check_out >= ref_date,
                PackageBooking.status != "cancelled"
            ).order_by(PackageBooking.id.desc()).first()
            
            if pkg_booking:
                order.package_booking_id = pkg_booking.id

        # Assigned Services
        services = db.query(AssignedService).filter(AssignedService.booking_id == None, AssignedService.package_booking_id == None).all()
        print(f"Found {len(services)} services to migrate.")
        for svc in services:
            ref_dt = svc.assigned_at
            if not ref_dt: continue
            ref_date = ref_dt.date()
            
            booking = db.query(Booking).join(BookingRoom).filter(
                BookingRoom.room_id == svc.room_id,
                Booking.check_in <= ref_date,
                Booking.check_out >= ref_date,
                Booking.status != "cancelled"
            ).order_by(Booking.id.desc()).first()
            
            if booking:
                svc.booking_id = booking.id
                continue
                
            pkg_booking = db.query(PackageBooking).join(PackageBookingRoom).filter(
                PackageBookingRoom.room_id == svc.room_id,
                PackageBooking.check_in <= ref_date,
                PackageBooking.check_out >= ref_date,
                PackageBooking.status != "cancelled"
            ).order_by(PackageBooking.id.desc()).first()
            
            if pkg_booking:
                svc.package_booking_id = pkg_booking.id
        
        # 3. Stock Issues Migration (Notes based)
        import re
        from app.models.inventory import StockIssue
        
        issues = db.query(StockIssue).filter(StockIssue.booking_id == None).all()
        print(f"Checking {len(issues)} stock issues for booking references in notes.")
        for issue in issues:
            if not issue.notes: continue
            
            # Simple regex to find BK-XXXXXX or PK-XXXXXX
            match = re.search(r'(BK|PK)-(\d+)', issue.notes.upper())
            if match:
                prefix = match.group(1)
                bid = int(match.group(2))
                
                if prefix == 'BK':
                    booking = db.query(Booking).filter(Booking.id == bid).first()
                    if booking:
                        issue.booking_id = booking.id
                        print(f"Linked Issue {issue.issue_number} to Booking {bid}")
                elif prefix == 'PK':
                    pbooking = db.query(PackageBooking).filter(PackageBooking.id == bid).first()
                    if pbooking:
                        # For now, we store in booking_id as well, or use a separate column if we had one
                        # Most logic currently looks at booking_id.
                        issue.booking_id = bid 
                        print(f"Linked Issue {issue.issue_number} to Package Booking {bid}")
        db.commit()
        print("Data migration completed successfully.")
    except Exception as e:
        db.rollback()
        print(f"Migration error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
