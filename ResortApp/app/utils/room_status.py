from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, DisconnectionError
from app.models.room import Room
from app.models.booking import Booking, BookingRoom
from datetime import date
import time

def update_room_statuses(db: Session):
    """
    Update room statuses based on current bookings.
    Only shows current day status - not future bookings.
    With improved error handling and retry logic.
    """
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            today = date.today()
            
            # Use with_for_update(nowait=True) to prevent deadlocks, but fallback if it fails
            try:
                rooms = db.query(Room).with_for_update(skip_locked=True).all()
            except Exception:
                # Fallback to regular query if row-level locking fails
                rooms = db.query(Room).all()
            
            updated_count = 0
            for room in rooms:
                try:
                    # FIX: Prioritize 'checked-in' status regarding of dates (handles checkout day and overstays)
                    
                    # 1. Check for Active Check-ins
                    active_checked_in = db.query(BookingRoom).join(Booking).filter(
                        BookingRoom.room_id == room.id,
                        Booking.status.in_(['checked-in', 'checked_in', 'Checked-in'])
                    ).first()
                    
                    from app.models.Package import PackageBooking, PackageBookingRoom
                    package_checked_in = db.query(PackageBookingRoom).join(PackageBooking).filter(
                        PackageBookingRoom.room_id == room.id,
                        PackageBooking.status.in_(['checked-in', 'checked_in', 'Checked-in'])
                    ).first()
                    
                    new_status = None
                    if active_checked_in or package_checked_in:
                         new_status = "Checked-in"
                    else:
                         # 2. Check for Active Reservations (Booked) - enforce dates
                         active_reservation = db.query(BookingRoom).join(Booking).filter(
                            BookingRoom.room_id == room.id,
                            Booking.status.in_(['booked', 'Booked']),
                            Booking.check_in <= today,
                            Booking.check_out > today
                        ).first()
                        
                         package_reservation = db.query(PackageBookingRoom).join(PackageBooking).filter(
                            PackageBookingRoom.room_id == room.id,
                            PackageBooking.status.in_(['booked', 'Booked']),
                            PackageBooking.check_in <= today,
                            PackageBooking.check_out > today
                        ).first()
                        
                         if active_reservation or package_reservation:
                             new_status = "Booked"
                         else:
                             new_status = "Available"
                    
                    # Only update if status changed to reduce unnecessary commits
                    if room.status != new_status:
                        room.status = new_status
                        updated_count += 1
                        
                except Exception as room_error:
                    # Log individual room errors but continue processing
                    print(f"Error updating room {room.id}: {room_error}")
                    continue
            
            try:
                db.commit()
            except Exception as commit_err:
                # Roll back any failed commit to avoid pending transaction errors
                db.rollback()
                print(f"Commit failed during room status update: {commit_err}")
                return 0
            if updated_count > 0:
                print(f"Updated room statuses for {updated_count} out of {len(rooms)} rooms")
            return updated_count
            
        except (OperationalError, DisconnectionError) as e:
            db.rollback()
            if attempt < max_retries - 1:
                print(f"Database error (attempt {attempt + 1}/{max_retries}): {e}. Retrying...")
                time.sleep(retry_delay * (attempt + 1))
                # Try to refresh the session
                db.expire_all()
                continue
            else:
                print(f"Error updating room statuses after {max_retries} attempts: {e}")
                # Don't raise - let the endpoint handle gracefully
                return 0
        except Exception as e:
            db.rollback()
            print(f"Error updating room statuses: {e}")
            print(f"Error type: {type(e)}")
            # Don't raise - allow room fetching to continue even if status update fails
            return 0
    
    return 0
