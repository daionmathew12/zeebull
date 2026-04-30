from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, DisconnectionError
from app.models.room import Room
from app.models.booking import Booking, BookingRoom
from app.models.Package import PackageBooking, PackageBookingRoom
from datetime import date, datetime, timedelta
from app.utils.date_utils import get_ist_today
import time

# Simple in-memory cache for throttling
_last_status_update = {}

def update_room_statuses(db: Session, branch_id: int = None):
    """
    Update room statuses based on current bookings.
    Only shows current day status - not future bookings.
    Optimized to use bulk queries instead of N+1 per room.
    """
    # Throttle: Only update once every 5 minutes per branch
    now = datetime.now()
    cache_key = branch_id or 0
    if cache_key in _last_status_update:
        if now - _last_status_update[cache_key] < timedelta(minutes=5):
            return 0
    
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            today = get_ist_today().date()
            
            # 1. Fetch rooms
            q_rooms = db.query(Room)
            if branch_id:
                q_rooms = q_rooms.filter(Room.branch_id == branch_id)
            rooms = q_rooms.all()
            if not rooms:
                return 0
            
            room_ids = [r.id for r in rooms]
            
            # 2. Bulk fetch active check-ins (Checked-in status takes precedence)
            checked_in_rooms = set()
            
            # Regular bookings
            active_checkins = db.query(BookingRoom.room_id).join(Booking).filter(
                BookingRoom.room_id.in_(room_ids),
                Booking.status.in_(['checked-in', 'checked_in', 'Checked-in'])
            ).all()
            for r in active_checkins:
                checked_in_rooms.add(r.room_id)
                
            # Package bookings
            pkg_checkins = db.query(PackageBookingRoom.room_id).join(PackageBooking).filter(
                PackageBookingRoom.room_id.in_(room_ids),
                PackageBooking.status.in_(['checked-in', 'checked_in', 'Checked-in'])
            ).all()
            for r in pkg_checkins:
                checked_in_rooms.add(r.room_id)
                
            # 3. Bulk fetch active reservations (Booked status for today)
            booked_rooms = set()
            
            # Regular bookings
            active_res = db.query(BookingRoom.room_id).join(Booking).filter(
                BookingRoom.room_id.in_(room_ids),
                Booking.status.in_(['booked', 'Booked']),
                Booking.check_in <= today,
                Booking.check_out > today
            ).all()
            for r in active_res:
                booked_rooms.add(r.room_id)
                
            # Package bookings
            pkg_res = db.query(PackageBookingRoom.room_id).join(PackageBooking).filter(
                PackageBookingRoom.room_id.in_(room_ids),
                PackageBooking.status.in_(['booked', 'Booked']),
                PackageBooking.check_in <= today,
                PackageBooking.check_out > today
            ).all()
            for r in pkg_res:
                booked_rooms.add(r.room_id)
            
            # 4. Update statuses in memory
            updated_count = 0
            for room in rooms:
                # Do not change status if it is Maintenance, Cleaning, or Dirty
                # Only change if it's Available, Checked-in, or Booked
                current_lower = room.status.lower()
                if current_lower in ["maintenance", "cleaning", "dirty"]:
                    continue
                    
                new_status = "Available"
                if room.id in checked_in_rooms:
                    new_status = "Checked-in"
                elif room.id in booked_rooms:
                    new_status = "Booked"
                
                if room.status != new_status:
                    room.status = new_status
                    updated_count += 1
            
            if updated_count > 0:
                db.commit()
                print(f"[STATUS] Optimized update: {updated_count} rooms updated.")
            
            # Update cache timestamp
            _last_status_update[cache_key] = now
            return updated_count
            
        except (OperationalError, DisconnectionError) as e:
            db.rollback()
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))
                continue
            else:
                print(f"Error updating room statuses: {e}")
                return 0
        except Exception as e:
            db.rollback()
            print(f"Error updating room statuses: {e}")
            return 0
    
    return 0

