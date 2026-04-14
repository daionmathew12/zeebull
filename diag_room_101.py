import os
import sys
from dotenv import load_dotenv

# Add the ResortApp directory to sys.path
sys.path.append('.')

# Load .env from the current directory
load_dotenv()

try:
    from app.database import SessionLocal
    from app.models.room import Room
    from app.models.inventory import LocationStock, AssetMapping, AssetRegistry, Location
    from app.models.booking import Booking
    from app.models.Package import PackageBooking
    from app.models.checkout import CheckoutRequest
except ImportError as e:
    print(f"Import Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

import json

db = SessionLocal()
room = db.query(Room).filter(Room.number == '101').first()
if not room:
    print('Room 101 not found')
else:
    print(f'Room 101 Inventory Location ID: {room.inventory_location_id}')
    if room.inventory_location_id:
        loc = db.query(Location).filter(Location.id == room.inventory_location_id).first()
        print(f'Location Name: {loc.name if loc else "Not Found"}')
        
        stocks = db.query(LocationStock).filter(LocationStock.location_id == room.inventory_location_id).all()
        print(f'LocationStock count: {len(stocks)}')
        for s in stocks:
            print(f'  - Item: {s.item.name if s.item else "Unknown"} (ID: {s.item_id}), Qty: {s.quantity}')
            
        mappings = db.query(AssetMapping).filter(AssetMapping.location_id == room.inventory_location_id).all()
        print(f'AssetMapping count: {len(mappings)}')
        for m in mappings:
            print(f'  - Item: {m.item.name if m.item else "Unknown"} (ID: {m.item_id}), Qty: {m.quantity}, IsActive: {m.is_active}')
            
        registry = db.query(AssetRegistry).filter(AssetRegistry.current_location_id == room.inventory_location_id).all()
        print(f'AssetRegistry count: {len(registry)}')
        for a in registry:
            print(f'  - Item: {a.item.name if a.item else "Unknown"} (ID: {a.item_id}), AssetTag: {a.asset_tag_id}, Status: {a.status}')

    # Check for ACTIVE Checkout Request for Room 101
    from sqlalchemy import desc
    req = db.query(CheckoutRequest).filter(CheckoutRequest.room_number == '101').order_by(desc(CheckoutRequest.created_at)).first()
    if req:
        print(f'Checkout Request Found: Room {req.room_number}, Guest {req.guest_name}, ID {req.id}, Status {getattr(req, "status", "N/A")}')
        booking_start = None
        if req.booking:
            print(f'  - Related Booking ID: {req.booking.id}, Guest: {req.booking.guest_name}, Check-in: {req.booking.checked_in_at or req.booking.check_in}')
            booking_start = req.booking.checked_in_at or req.booking.check_in
        elif req.package_booking:
            print(f'  - Related Package Booking ID: {req.package_booking.id}, Guest: {req.package_booking.guest_name}, Check-in: {req.package_booking.checked_in_at or req.package_booking.check_in}')
            booking_start = req.package_booking.checked_in_at or req.package_booking.check_in
        
        if booking_start:
            from datetime import datetime, timedelta
            if isinstance(booking_start, str):
                try: booking_start = datetime.fromisoformat(booking_start.replace('Z', '+00:00'))
                except: booking_start = datetime.strptime(booking_start, '%Y-%m-%d')
            
            # Print if its a datetime
            print(f"  - Parsed Booking Start: {booking_start}")
            
            # Check for stock issues in the last 48 hours (to be safe)
            from app.models.inventory import StockIssue, StockIssueDetail
            issues = db.query(StockIssue).filter(
                StockIssue.destination_location_id == room.inventory_location_id,
                StockIssue.issue_date >= (booking_start - timedelta(hours=24))
            ).all()
            print(f"  - Recent Stock Issues (since 24h before check-in): {len(issues)}")
            for issue in issues:
                details = db.query(StockIssueDetail).filter(StockIssueDetail.stock_issue_id == issue.id).all()
                for d in details:
                    print(f"    * Issued Item: {d.item.name if d.item else 'Unknown'} (ID: {d.item_id}), Qty: {d.issued_quantity}, Date: {issue.issue_date}")

    else:
        print('No checkout request found for Room 101')

db.close()
