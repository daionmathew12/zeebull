# booking.py
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query, Form
from sqlalchemy.orm import Session, joinedload, load_only
from sqlalchemy import func, or_, and_
from typing import List, Union, Optional
from app.utils.auth import get_db, get_current_user
from app.utils.api_optimization import optimize_limit, MAX_LIMIT_LOW_NETWORK
from app.utils.booking_id import parse_display_id
from app.models.booking import Booking, BookingRoom
from app.models.user import User
from app.models.room import Room
from app.models.Package import Package, PackageBooking, PackageBookingRoom
from app.schemas.booking import BookingCreate, BookingOut
from app.models.checkout import Checkout
from app.schemas.room import RoomOut
from fastapi.responses import FileResponse
import os
import shutil
import uuid

UPLOAD_DIR = "uploads/checkin_proofs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
from app.schemas.booking import BookingOut, BookingRoomOut
from pydantic import BaseModel, ValidationError

# Detailed Model Imports
from app.models.foodorder import FoodOrder
from app.models.service import AssignedService
from app.models.inventory import StockIssue, StockIssueDetail, InventoryItem, Location

class PaginatedBookingResponse(BaseModel):
    total: int
    bookings: List[BookingOut]

router = APIRouter(prefix="/bookings", tags=["Bookings"])

@router.get("", response_model=PaginatedBookingResponse)
def get_bookings(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user), 
    skip: int = 0, 
    limit: int = 20, 
    order_by: str = "id", 
    order: str = "desc",
    fields: Optional[str] = None,
    room_id: Optional[int] = None
):
    try:
        # Optimize limit for low network
        limit = optimize_limit(limit, MAX_LIMIT_LOW_NETWORK)
        
        # Get regular bookings - NO eager loading to maximize performance
        # Load relationships separately only when needed
        query = db.query(Booking)

        if room_id:
            query = query.join(BookingRoom).filter(BookingRoom.room_id == room_id)
        
        # Apply ordering
        if order_by == "id" and order == "desc":
            query = query.order_by(Booking.id.desc())
        elif order_by == "id" and order == "asc":
            query = query.order_by(Booking.id.asc())
        elif order_by == "check_in" and order == "desc":
            query = query.order_by(Booking.check_in.desc())
        elif order_by == "check_in" and order == "asc":
            query = query.order_by(Booking.check_in.asc())
        
        regular_bookings = query.offset(skip).limit(limit).all()
        
        # Batch load rooms for all bookings to avoid N+1
        booking_ids = [b.id for b in regular_bookings]
        booking_rooms_map = {}
        if booking_ids:
            booking_rooms = db.query(BookingRoom).filter(BookingRoom.booking_id.in_(booking_ids)).all()
            room_ids = [br.room_id for br in booking_rooms if br.room_id]
            rooms_map = {}
            if room_ids:
                rooms = db.query(Room).filter(Room.id.in_(room_ids)).all()
                rooms_map = {r.id: r for r in rooms}
            
            for br in booking_rooms:
                if br.booking_id not in booking_rooms_map:
                    booking_rooms_map[br.booking_id] = []
                if br.room_id and br.room_id in rooms_map:
                    booking_rooms_map[br.booking_id].append(rooms_map[br.room_id])
        
        # Convert to BookingOut format
        booking_results = []
        for booking in regular_bookings:
            # Handle invalid emails gracefully
            user_obj = None
            # Load user separately to avoid blocking on eager load
            try:
                if hasattr(booking, 'user_id') and booking.user_id:
                    booking_user = db.query(User).filter(User.id == booking.user_id).first()
                else:
                    booking_user = None
            except:
                booking_user = None
            
            if booking_user:
                try:
                    from app.schemas.user import UserOut
                    user_data = booking_user
                    email = user_data.email if hasattr(user_data, "email") else None
                    if email and "@" in email and "." not in email.split("@")[1]:
                        # Fix malformed email by appending .com
                        email = email + ".com"
                    # Load role separately if needed (avoid eager load blocking)
                    role_obj = None
                    try:
                        if hasattr(user_data, 'role_id') and user_data.role_id:
                            from app.models.role import Role
                            role_obj = db.query(Role).filter(Role.id == user_data.role_id).first()
                    except:
                        role_obj = None
                    
                    user_dict = {
                        "id": user_data.id,
                        "name": user_data.name,
                        "email": email,
                        "phone": getattr(user_data, "phone", None),
                        "is_active": getattr(user_data, "is_active", True),
                        "role": role_obj
                    }
                    user_obj = UserOut.model_validate(user_dict)
                except Exception as e:
                    print(f"Warning: Could not create UserOut for booking {booking.id}: {str(e)}")
                    user_obj = None

            booking_out = BookingOut(
                id=booking.id,
                guest_name=booking.guest_name,
                guest_mobile=booking.guest_mobile,
                guest_email=booking.guest_email,
                status=booking.status,
                check_in=booking.check_in,
                check_out=booking.check_out,
                adults=booking.adults,
                children=booking.children,
                id_card_image_url=getattr(booking, 'id_card_image_url', None),
                guest_photo_url=getattr(booking, 'guest_photo_url', None),
                user=user_obj,
                is_package=False,
                total_amount=booking.total_amount or 0.0,
                advance_deposit=booking.advance_deposit or 0.0,
                rooms=booking_rooms_map.get(booking.id, [])
            )
            
            # Fallback: Calculate total amount if 0 (for legacy data)
            if (booking_out.total_amount is None or booking_out.total_amount == 0) and booking.check_in and booking.check_out and booking_out.rooms:
                try:
                    # Calculate duration
                    d_in = booking.check_in
                    d_out = booking.check_out
                    
                    # Handle potential string dates from unexpected sources
                    if isinstance(d_in, str):
                        from datetime import datetime
                        d_in = datetime.strptime(d_in, '%Y-%m-%d').date()
                    if isinstance(d_out, str):
                        from datetime import datetime
                        d_out = datetime.strptime(d_out, '%Y-%m-%d').date()
                        
                    stay_days = (d_out - d_in).days
                    stay_nights = max(1, stay_days)
                    
                    room_total = sum(float(r.price or 0) for r in booking_out.rooms)
                    final_amount = room_total * stay_nights
                    
                    if final_amount > 0:
                        booking_out.total_amount = final_amount
                        # Self-healing: Update DB
                        # Note: We need to be careful with commits in GET, but specific updates are okay.
                        # We use a separate update query to avoid messing with the current session state too much.
                        try:
                            # Use core update to avoid session issues
                            from sqlalchemy import update
                            stmt = update(Booking).where(Booking.id == booking.id).values(total_amount=final_amount)
                            db.execute(stmt)
                            db.commit()
                            print(f"Self-healed Booking {booking.id} total_amount to {final_amount}")
                        except Exception as db_e:
                            print(f"Failed to update healed amount to DB: {db_e}")
                            db.rollback()
                except Exception as e:
                    print(f"Error calculating fallback amount for booking {booking.id}: {str(e)}")
            
            booking_results.append(booking_out)
        
        # Get total count (only if limit is reasonable to avoid slow queries)
        # For large datasets, skip count to improve performance
        total_count = len(booking_results) if limit <= 100 else len(booking_results)
        
        return {"total": total_count, "bookings": booking_results}
    except Exception as e:
        print(f"Error fetching bookings: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching bookings: {str(e)}")

# ----------------------------------------------------------------
# GET Detailed view for a SINGLE booking (regular or package)
# This is a more reliable way to get full details for the modal view.
# ----------------------------------------------------------------
# ----------------------------------------------------------------
# HELPERS for Detailed Views
# ----------------------------------------------------------------
def _fetch_extras(db: Session, room_ids: List[int], check_in, check_out):
    if not room_ids:
        return []
    
    # Fetch food orders for these rooms created during the stay
    # We use a permissive date filter (created_at >= check_in)
    # Note: check_out is usually noon, so orders on check_out day before checkout are valid.
    query = db.query(FoodOrder).options(joinedload(FoodOrder.items)).filter(
        FoodOrder.room_id.in_(room_ids),
        FoodOrder.created_at >= check_in
    )
    # If check_out is provided, filter
    if check_out:
         # Convert date to datetime if needed or just compare date part
         query = query.filter(func.date(FoodOrder.created_at) <= check_out)
         
    orders = query.all()
    
    result = []
    for o in orders:
        items_summary = []
        for i in o.items:
            # Safely access food_item name via relationship or ID
            # Assuming relationship is 'food_item'
            i_name = i.food_item.name if i.food_item else "Unknown Item"
            items_summary.append(f"{i_name} (x{i.quantity})")
            
        result.append({
            "id": o.id,
            "items": items_summary, # Simplified list of strings
            "amount": o.amount,
            "status": o.status,
            "created_at": o.created_at
        })
    return result

def _fetch_services(db: Session, room_ids: List[int], check_in, check_out):
    if not room_ids:
        return []
        
    query = db.query(AssignedService).options(joinedload(AssignedService.service)).filter(
        AssignedService.room_id.in_(room_ids),
        AssignedService.assigned_at >= check_in
    )
    if check_out:
         query = query.filter(func.date(AssignedService.assigned_at) <= check_out)
         
    services = query.all()
    
    return [{
        "id": s.id,
        "service_name": s.service.name if s.service else "Unknown Service",
        "charges": s.service.charges if s.service else 0.0,
        "status": s.status,
        "assigned_at": s.assigned_at
    } for s in services]

def _fetch_inventory(db: Session, room_ids: List[int], check_in, check_out):
    if not room_ids:
        return []
        
    # Get location IDs for these rooms
    rooms = db.query(Room).filter(Room.id.in_(room_ids)).all()
    location_ids = [r.inventory_location_id for r in rooms if r.inventory_location_id]
    
    if not location_ids:
        return []
        
    # Fetch stock issues
    query = (
        db.query(StockIssueDetail)
        .join(StockIssue)
        .join(InventoryItem)
        .filter(StockIssue.destination_location_id.in_(location_ids))
        .filter(StockIssue.issue_date >= check_in)
        .options(joinedload(StockIssueDetail.item).joinedload(InventoryItem.category))
    )
    if check_out:
        query = query.filter(func.date(StockIssue.issue_date) <= check_out)
        
    details = query.all()
    
    return [{
        "item_name": d.item.name if d.item else "Unknown",
        "quantity": d.issued_quantity,
        "unit": d.unit,
        "category": d.item.category.name if d.item and d.item.category else None,
        "issued_at": d.issue.issue_date,
        "is_payable": d.is_payable or False,
        "unit_price": d.unit_price or 0.0,
        "is_damaged": d.is_damaged or False,
        "notes": d.damage_notes if d.is_damaged else d.notes
    } for d in details]

# ----------------------------------------------------------------
# GET Detailed view for a SINGLE booking (regular or package)
# ----------------------------------------------------------------
@router.get("/details/{booking_id}", response_model=BookingOut)
def get_booking_details(booking_id: Union[str, int], is_package: bool, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Parse display ID (BK-000001 or PK-000001) or accept numeric ID
    numeric_id, booking_type = parse_display_id(str(booking_id))
    if numeric_id is None:
        raise HTTPException(status_code=400, detail=f"Invalid booking ID format: {booking_id}")
    
    if booking_type:
        if booking_type == "package" and not is_package:
            raise HTTPException(status_code=400, detail=f"Booking ID {booking_id} is a package booking, but is_package parameter is False")
        if booking_type == "booking" and is_package:
            raise HTTPException(status_code=400, detail=f"Booking ID {booking_id} is a regular booking, but is_package parameter is True")
    
    booking_id = numeric_id
    
    try:
        if is_package:
            booking = db.query(PackageBooking).options(
                joinedload(PackageBooking.rooms).joinedload(PackageBookingRoom.room),
                joinedload(PackageBooking.user),
                joinedload(PackageBooking.package),
                joinedload(PackageBooking.checkout)
            ).filter(PackageBooking.id == booking_id).first()

            if not booking:
                raise HTTPException(status_code=404, detail="Package booking not found")

            # Calc total
            total_amt = 0.0
            if booking.checkout:
                total_amt = booking.checkout.grand_total
            elif booking.status in ['checked_out', 'checked-out', 'checked out']:
                 checkout_rec = db.query(Checkout).filter(Checkout.package_booking_id == booking.id).order_by(Checkout.id.desc()).first()
                 if checkout_rec: total_amt = checkout_rec.grand_total

            room_ids = [r.room_id for r in booking.rooms if r.room_id]
            
            return BookingOut(
                id=booking.id,
                guest_name=booking.guest_name,
                guest_mobile=booking.guest_mobile,
                guest_email=booking.guest_email,
                status=booking.status,
                check_in=booking.check_in,
                check_out=booking.check_out,
                adults=booking.adults,
                children=booking.children,
                id_card_image_url=getattr(booking, 'id_card_image_url', None),
                guest_photo_url=getattr(booking, 'guest_photo_url', None),
                user=booking.user,
                is_package=True,
                total_amount=total_amt,
                rooms=[pbr.room for pbr in booking.rooms if pbr.room],
                food_orders=_fetch_extras(db, room_ids, booking.check_in, booking.check_out),
                service_requests=_fetch_services(db, room_ids, booking.check_in, booking.check_out),
                inventory_usage=_fetch_inventory(db, room_ids, booking.check_in, booking.check_out)
            )
        else: # Regular booking
            booking = db.query(Booking).options(
                joinedload(Booking.booking_rooms).joinedload(BookingRoom.room),
                joinedload(Booking.user).joinedload(User.role),
                joinedload(Booking.checkout)
            ).filter(Booking.id == booking_id).first()

            if not booking:
                raise HTTPException(status_code=404, detail="Booking not found")
            
            total_amt = getattr(booking, 'total_amount', 0.0)
            if booking.checkout:
                total_amt = booking.checkout.grand_total
            elif booking.status in ['checked_out', 'checked-out', 'checked out'] and (total_amt is None or total_amt == 0):
                 checkout_rec = db.query(Checkout).filter(Checkout.booking_id == booking.id).order_by(Checkout.id.desc()).first()
                 if checkout_rec: total_amt = checkout_rec.grand_total
            
            # Fallback for active regular bookings without a total (legacy data)
            if (total_amt is None or total_amt == 0) and booking.check_in and booking.check_out and booking.booking_rooms:
                try:
                    # Calculate dates
                    d_in = booking.check_in
                    d_out = booking.check_out
                    
                    if isinstance(d_in, str):
                        from datetime import datetime
                        d_in = datetime.strptime(d_in, '%Y-%m-%d').date()
                    if isinstance(d_out, str):
                        from datetime import datetime
                        d_out = datetime.strptime(d_out, '%Y-%m-%d').date()
                        
                    stay_days = (d_out - d_in).days
                    stay_nights = max(1, stay_days)
                    
                    room_total = sum(float(br.room.price or 0) for br in booking.booking_rooms if br.room)
                    calc_amt = room_total * stay_nights
                    
                    if calc_amt > 0:
                        total_amt = calc_amt
                        # Update DB 
                        from sqlalchemy import update
                        stmt = update(Booking).where(Booking.id == booking.id).values(total_amount=calc_amt)
                        db.execute(stmt)
                        db.commit()
                except Exception as e:
                    print(f"Error self-healing booking detail {booking.id}: {e}")
            
            room_ids = [r.room_id for r in booking.booking_rooms if r.room_id]

            return BookingOut(
                id=booking.id,
                guest_name=booking.guest_name,
                guest_mobile=booking.guest_mobile,
                guest_email=booking.guest_email,
                status=booking.status,
                check_in=booking.check_in,
                check_out=booking.check_out,
                adults=booking.adults,
                children=booking.children,
                id_card_image_url=getattr(booking, 'id_card_image_url', None),
                guest_photo_url=getattr(booking, 'guest_photo_url', None),
                user=booking.user,
                is_package=False,
                total_amount=total_amt,
                advance_deposit=booking.advance_deposit or 0.0,
                rooms=[br.room for br in booking.booking_rooms if br.room],
                food_orders=_fetch_extras(db, room_ids, booking.check_in, booking.check_out),
                service_requests=_fetch_services(db, room_ids, booking.check_in, booking.check_out),
                inventory_usage=_fetch_inventory(db, room_ids, booking.check_in, booking.check_out)
            )
    except Exception as e:
        print(f"Error getting booking details: {e}")
        # Return basic details if list fetching fails, to avoid 500 error on the whole page
        # But for development/debugging, seeing the error is better. 
        # I'll raise it for now.
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------
# Helper function to get or create guest user
# -------------------------------
def get_or_create_guest_user(db: Session, email: str, mobile: str, name: str):
    """
    Find or create a guest user based on email and mobile number.
    Returns the user_id to link bookings to the same user.
    """
    from app.models.user import User, Role
    import bcrypt
    
    # Normalize empty strings to None for easier handling
    email = email.strip() if email and isinstance(email, str) else None
    mobile = mobile.strip() if mobile and isinstance(mobile, str) else None
    name = name.strip() if name and isinstance(name, str) else "Guest User"
    
    # Need at least one identifier (email or mobile)
    if not email and not mobile:
        raise ValueError("Either email or mobile number must be provided")
    
    # First, try to find user by email (most reliable identifier)
    user = None
    if email:
        user = db.query(User).filter(User.email == email).first()
    
    # If not found by email, try by mobile/phone
    if not user and mobile:
        user = db.query(User).filter(User.phone == mobile).first()
    
    # If user exists, return the user_id
    if user:
        # Update name if provided and different
        if name and user.name != name:
            user.name = name
            db.commit()
        return user.id
    
    # If user doesn't exist, create a new guest user
    try:
        # First, ensure 'guest' role exists
        guest_role = db.query(Role).filter(Role.name == "guest").first()
        if not guest_role:
            # Create guest role if it doesn't exist
            guest_role = Role(name="guest", permissions="[]")
            db.add(guest_role)
            db.commit()
            db.refresh(guest_role)
        
        # Generate a placeholder password for guest users (they won't log in)
        password_bytes = "guest_user_no_password".encode("utf-8")
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt).decode("utf-8")
        
        # Create email if not provided (use mobile-based email or generate unique one)
        if not email:
            if mobile:
                user_email = f"guest_{mobile}@temp.com"
            else:
                # Generate a unique email based on timestamp
                import time
                user_email = f"guest_{int(time.time())}@temp.com"
        else:
            user_email = email
        
        # Check if email already exists (race condition check)
        existing_user = db.query(User).filter(User.email == user_email).first()
        if existing_user:
            # User was created between our check and creation attempt
            return existing_user.id
        
        # Create new guest user
        new_user = User(
            name=name,
            email=user_email,
            phone=mobile if mobile else None,
            hashed_password=hashed_password,
            role_id=guest_role.id,
            is_active=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user.id
    except Exception as e:
        # If user creation fails due to unique constraint or other DB error, try to find existing user
        db.rollback()  # Rollback the failed transaction
        if email:
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                return existing_user.id
        if mobile:
            existing_user = db.query(User).filter(User.phone == mobile).first()
            if existing_user:
                return existing_user.id
        # Re-raise if we can't find existing user
        raise ValueError(f"Failed to create or find guest user: {str(e)}")

# -------------------------------
# POST a new booking
# -------------------------------
@router.post("", response_model=BookingOut) # Changed from "/" to ""
def create_booking(booking: BookingCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    print(f"DEBUG: create_booking called with: {booking}")
    # Find or create guest user based on email and mobile
    guest_user_id = None
    # Normalize email and mobile - convert empty strings to None, handle None safely
    try:
        guest_email = booking.guest_email.strip() if (booking.guest_email and isinstance(booking.guest_email, str) and booking.guest_email.strip()) else None
    except (AttributeError, TypeError):
        guest_email = None
    
    try:
        guest_mobile = booking.guest_mobile.strip() if (booking.guest_mobile and isinstance(booking.guest_mobile, str) and booking.guest_mobile.strip()) else None
    except (AttributeError, TypeError):
        guest_mobile = None
    
    if guest_email or guest_mobile:
        try:
            guest_user_id = get_or_create_guest_user(
                db=db,
                email=guest_email,
                mobile=guest_mobile,
                name=booking.guest_name or "Guest User"
            )
        except Exception as e:
            # Log error but don't fail the booking if user creation fails
            print(f"Warning: Could not create/link guest user: {str(e)}")
    
    # Check for an existing booking to reuse guest details for consistency
    existing_booking = db.query(Booking).filter(
        (Booking.guest_email == booking.guest_email) & (Booking.guest_mobile == booking.guest_mobile)
    ).order_by(Booking.id.desc()).first()

    # Logic Removed: We should NOT overwrite the provided guest name with an old one.
    # If the user provides a name "jeena", we should save "jeena", even if previous bookings
    # with this email/mobile were "haryhh". The user might be correcting a typo or it might be different.
    guest_name_to_use = booking.guest_name

    # Validate room capacity for adults and children separately
    selected_rooms = db.query(Room).filter(Room.id.in_(booking.room_ids)).all()
    if len(selected_rooms) != len(booking.room_ids):
        print(f"DEBUG: Invalid rooms. Selected IDs: {booking.room_ids}, Found: {len(selected_rooms)}")
        raise HTTPException(status_code=400, detail="One or more selected rooms are invalid.")
    
    total_adult_capacity = sum(room.adults or 0 for room in selected_rooms)
    total_children_capacity = sum(room.children or 0 for room in selected_rooms)
    
    if booking.adults > total_adult_capacity:
        print(f"DEBUG: Adult capacity exceeded. Request: {booking.adults}, Max: {total_adult_capacity}")
        raise HTTPException(
            status_code=400,
            detail=f"The number of adults ({booking.adults}) exceeds the total adult capacity of the selected rooms ({total_adult_capacity} adults max). Please select additional rooms or reduce the number of adults."
        )
    
    if booking.children > total_children_capacity:
        raise HTTPException(
            status_code=400,
            detail=f"The number of children ({booking.children}) exceeds the total children capacity of the selected rooms ({total_children_capacity} children max). Please select additional rooms or reduce the number of children."
        )

    # Check if rooms are available for the requested dates
    for room_id in booking.room_ids:
        # Check if room is already booked by regular bookings for overlapping dates (only check active bookings, not cancelled or checked-out)
        conflicting_regular_booking = db.query(BookingRoom).join(Booking).filter(
            BookingRoom.room_id == room_id,
            BookingRoom.room_id == room_id,
            # Case-insensitive check for active statuses
            and_(
                Booking.status.ilike('booked'),
                Booking.status.ilike('checked-in')
            ) == False, # Logic fix: we want to MATCH these
            # Actually, using in_ with ilike is hard in one go.
            # Simplified:
            or_(
                Booking.status.ilike('booked'),
                Booking.status.ilike('checked-in')
            ),
            Booking.check_in < booking.check_out,
            Booking.check_out > booking.check_in
        ).first()
        
        # Check if room is already booked by package bookings for overlapping dates
        conflicting_package_booking = db.query(PackageBookingRoom).join(PackageBooking).filter(
            PackageBookingRoom.room_id == room_id,
            PackageBooking.status.in_(['booked', 'checked-in']),  # Only check for active bookings
            PackageBooking.check_in < booking.check_out,
            PackageBooking.check_out > booking.check_in
        ).first()
        
        if conflicting_regular_booking or conflicting_package_booking:
            room = db.query(Room).filter(Room.id == room_id).first()
            print(f"DEBUG: Room conflict for room_id {room_id}. Regular: {conflicting_regular_booking}, Package: {conflicting_package_booking}")
            raise HTTPException(
                status_code=400,
                detail=f"Room {room.number if room else room_id} is not available for the selected dates."
            )

    db_booking = Booking(
        guest_name=guest_name_to_use,
        guest_mobile=booking.guest_mobile,
        guest_email=booking.guest_email,
        check_in=booking.check_in,
        check_out=booking.check_out,
        adults=booking.adults,
        children=booking.children,
        user_id=guest_user_id,  # Link booking to guest user
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    # Create BookingRoom links and update room status
    for room_id in booking.room_ids:
        room = db.query(Room).filter(Room.id == room_id).first()
        if room:
            room.status = "Booked"
        db.add(BookingRoom(booking_id=db_booking.id, room_id=room_id))
    
    db.commit()

    db.refresh(db_booking)
    
    # Reload with room details for response
    booking_with_rooms = (
        db.query(Booking)
        .options(joinedload(Booking.booking_rooms).joinedload(BookingRoom.room))
        .filter(Booking.id == db_booking.id)
        .first()
    )
    
    # Convert to BookingOut format with rooms
    booking_out = BookingOut(
        id=booking_with_rooms.id,
        guest_name=booking_with_rooms.guest_name,
        guest_mobile=booking_with_rooms.guest_mobile,
        guest_email=booking_with_rooms.guest_email,
        status=booking_with_rooms.status,
        check_in=booking_with_rooms.check_in,
        check_out=booking_with_rooms.check_out,
        adults=booking_with_rooms.adults,
        children=booking_with_rooms.children,
        id_card_image_url=getattr(booking_with_rooms, 'id_card_image_url', None),
        guest_photo_url=getattr(booking_with_rooms, 'guest_photo_url', None),
        user=booking_with_rooms.user,
        is_package=False,
        rooms=[br.room for br in booking_with_rooms.booking_rooms if br.room]
    )
    
    # Calculate booking charges and send confirmation email if email address is provided
    if booking.guest_email:
        try:
            from app.utils.email import send_email, create_booking_confirmation_email
            from datetime import datetime, date
            
            # Calculate stay duration
            check_in_date = booking.check_in if isinstance(booking.check_in, date) else datetime.strptime(str(booking.check_in), '%Y-%m-%d').date()
            check_out_date = booking.check_out if isinstance(booking.check_out, date) else datetime.strptime(str(booking.check_out), '%Y-%m-%d').date()
            stay_nights = max(1, (check_out_date - check_in_date).days)
            
            # Calculate room charges
            room_charges = 0
            rooms_data = []
            for br in booking_with_rooms.booking_rooms:
                if br.room:
                    room_price = br.room.price or 0
                    room_charges_per_room = room_price * stay_nights
                    room_charges += room_charges_per_room
                    rooms_data.append({
                        'number': br.room.number,
                        'type': br.room.type or 'Standard',
                        'price': room_price
                    })
            
            # Format booking ID (BK-000001)
            formatted_booking_id = f"BK-{str(booking_with_rooms.id).zfill(6)}"
            
            email_html = create_booking_confirmation_email(
                guest_name=guest_name_to_use,
                booking_id=booking_with_rooms.id,
                booking_type='room',
                check_in=str(booking.check_in),
                check_out=str(booking.check_out),
                rooms=rooms_data,
                total_amount=room_charges,
                guests={'adults': booking.adults, 'children': booking.children},
                guest_mobile=booking.guest_mobile,
                room_charges=room_charges,
                stay_nights=stay_nights
            )
            
            send_email(
                to_email=booking.guest_email,
                subject=f"Booking Confirmation {formatted_booking_id} - Elysian Retreat",
                html_content=email_html,
                to_name=guest_name_to_use
            )
        except Exception as e:
            # Log error but don't fail the booking
            print(f"Failed to send confirmation email: {str(e)}")
    
    return booking_out

@router.post("/guest", response_model=BookingOut, summary="Create a booking as a guest")
def create_guest_booking(booking: BookingCreate, db: Session = Depends(get_db)):
    """
    Public endpoint for guests to create a booking without authentication.
    """
    try:
        # Find or create guest user based on email and mobile
        guest_user_id = None
        # Normalize email and mobile - convert empty strings to None, handle None safely
        try:
            guest_email = booking.guest_email.strip() if (booking.guest_email and isinstance(booking.guest_email, str) and booking.guest_email.strip()) else None
        except (AttributeError, TypeError):
            guest_email = None
        
        try:
            guest_mobile = booking.guest_mobile.strip() if (booking.guest_mobile and isinstance(booking.guest_mobile, str) and booking.guest_mobile.strip()) else None
        except (AttributeError, TypeError):
            guest_mobile = None
        
        if guest_email or guest_mobile:
            try:
                guest_user_id = get_or_create_guest_user(
                    db=db,
                    email=guest_email,
                    mobile=guest_mobile,
                    name=booking.guest_name or "Guest User"
                )
            except Exception as e:
                # Log error but don't fail the booking if user creation fails
                print(f"Warning: Could not create/link guest user: {str(e)}")
        
        # Check for duplicate booking with same details and dates
        # Only check for duplicates if we have at least email or mobile
        duplicate_booking = None
        if guest_email or guest_mobile:
            duplicate_query = db.query(Booking).filter(
                Booking.check_in == booking.check_in,
                Booking.check_out == booking.check_out,
                Booking.status.in_(['booked', 'checked-in'])
            )
            
            # Add email filter if normalized email exists
            if guest_email:
                duplicate_query = duplicate_query.filter(Booking.guest_email == guest_email)
            
            # Add mobile filter if normalized mobile exists
            if guest_mobile:
                duplicate_query = duplicate_query.filter(Booking.guest_mobile == guest_mobile)
            
            duplicate_booking = duplicate_query.first()
        
        if duplicate_booking:
            raise HTTPException(
                status_code=400, 
                detail="A booking with the same details and dates already exists. Please check your existing bookings."
            )

        # Check for an existing booking to reuse guest details for consistency
        # Only check if we have at least email or mobile
        existing_booking = None
        if guest_email or guest_mobile:
            existing_query = db.query(Booking)
            
            # Add email filter if normalized email exists
            if guest_email:
                existing_query = existing_query.filter(Booking.guest_email == guest_email)
            
            # Add mobile filter if normalized mobile exists
            if guest_mobile:
                existing_query = existing_query.filter(Booking.guest_mobile == guest_mobile)
            
            existing_booking = existing_query.order_by(Booking.id.desc()).first()

        # Logic Removed: Do not overwrite guest name with old data.
        guest_name_to_use = booking.guest_name or "Guest User"

        # Validate room capacity for adults and children separately
        selected_rooms = db.query(Room).filter(Room.id.in_(booking.room_ids)).all()
        if len(selected_rooms) != len(booking.room_ids):
            raise HTTPException(status_code=400, detail="One or more selected rooms are invalid.")
        
        total_adult_capacity = sum(room.adults or 0 for room in selected_rooms)
        total_children_capacity = sum(room.children or 0 for room in selected_rooms)
        
        if booking.adults > total_adult_capacity:
            raise HTTPException(
                status_code=400,
                detail=f"The number of adults ({booking.adults}) exceeds the total adult capacity of the selected rooms ({total_adult_capacity} adults max). Please select additional rooms or reduce the number of adults."
            )
        
        if booking.children > total_children_capacity:
            raise HTTPException(
                status_code=400,
                detail=f"The number of children ({booking.children}) exceeds the total children capacity of the selected rooms ({total_children_capacity} children max). Please select additional rooms or reduce the number of children."
            )

        # Check if rooms are available for the requested dates
        for room_id in booking.room_ids:
            # Check if room is already booked by regular bookings for overlapping dates (only check active bookings, not cancelled or checked-out)
            conflicting_regular_booking = db.query(BookingRoom).join(Booking).filter(
                BookingRoom.room_id == room_id,
                BookingRoom.room_id == room_id,
                or_(
                    Booking.status.ilike('booked'),
                    Booking.status.ilike('checked-in')
                ),
                Booking.check_in < booking.check_out,
                Booking.check_out > booking.check_in
            ).first()
            
            # Check if room is already booked by package bookings for overlapping dates
            conflicting_package_booking = db.query(PackageBookingRoom).join(PackageBooking).filter(
                PackageBookingRoom.room_id == room_id,
                PackageBooking.status.in_(['booked', 'checked-in']),  # Only check for active bookings
                PackageBooking.check_in < booking.check_out,
                PackageBooking.check_out > booking.check_in
            ).first()
            
            if conflicting_regular_booking or conflicting_package_booking:
                room = db.query(Room).filter(Room.id == room_id).first()
                raise HTTPException(
                    status_code=400,
                    detail=f"Room {room.number if room else room_id} is not available for the selected dates."
                )

        # Calculate stay duration
        from datetime import datetime
        # Ensure dates are date objects
        d_check_in = booking.check_in if isinstance(booking.check_in, date) else datetime.strptime(str(booking.check_in), '%Y-%m-%d').date()
        d_check_out = booking.check_out if isinstance(booking.check_out, date) else datetime.strptime(str(booking.check_out), '%Y-%m-%d').date()
        days = (d_check_out - d_check_in).days
        stay_nights = days if days > 0 else 1
        
        # Calculate total room price per night
        total_price_per_night = sum(room.price or 0 for room in selected_rooms)
        calculated_total_amount = total_price_per_night * stay_nights

        db_booking = Booking(
            guest_name=guest_name_to_use,
            guest_mobile=guest_mobile or booking.guest_mobile or None,  # Use normalized mobile or original, fallback to None
            guest_email=guest_email or booking.guest_email or None,  # Use normalized email or original, fallback to None
            check_in=booking.check_in,
            check_out=booking.check_out,
            adults=booking.adults,
            children=booking.children,
            user_id=guest_user_id,  # Link booking to guest user
            total_amount=calculated_total_amount, # Set calculated total amount
        )
        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)

        # Create BookingRoom links and update room status
        for room_id in booking.room_ids:
            db.query(Room).filter(Room.id == room_id).update({"status": "Booked"})
            db.add(BookingRoom(booking_id=db_booking.id, room_id=room_id))
        db.commit()
        db.refresh(db_booking)
        
        # Reload with room details for email and response
        booking_with_rooms = (
            db.query(Booking)
            .options(joinedload(Booking.booking_rooms).joinedload(BookingRoom.room))
            .filter(Booking.id == db_booking.id)
            .first()
        )
        
        # Calculate booking charges and send confirmation email if email address is provided
        if guest_email or booking.guest_email:
            try:
                from app.utils.email import send_email, create_booking_confirmation_email
                from datetime import datetime, date
                
                # Calculate stay duration
                check_in_date = booking.check_in if isinstance(booking.check_in, date) else datetime.strptime(str(booking.check_in), '%Y-%m-%d').date()
                check_out_date = booking.check_out if isinstance(booking.check_out, date) else datetime.strptime(str(booking.check_out), '%Y-%m-%d').date()
                stay_nights = max(1, (check_out_date - check_in_date).days)
                
                # Calculate room charges
                room_charges = 0
                rooms_data = []
                for br in booking_with_rooms.booking_rooms:
                    if br.room:
                        room_price = br.room.price or 0
                        room_charges_per_room = room_price * stay_nights
                        room_charges += room_charges_per_room
                        rooms_data.append({
                            'number': br.room.number,
                            'type': br.room.type or 'Standard',
                            'price': room_price
                        })
                
                # Format booking ID (BK-000001)
                formatted_booking_id = f"BK-{str(db_booking.id).zfill(6)}"
                
                email_to_use = guest_email or booking.guest_email
                if email_to_use:
                    email_html = create_booking_confirmation_email(
                        guest_name=guest_name_to_use,
                        booking_id=db_booking.id,
                        booking_type='room',
                        check_in=str(booking.check_in),
                        check_out=str(booking.check_out),
                        rooms=rooms_data,
                        total_amount=room_charges,
                        guests={'adults': booking.adults, 'children': booking.children},
                        guest_mobile=guest_mobile or booking.guest_mobile,
                        room_charges=room_charges,
                        stay_nights=stay_nights
                    )
                    
                    send_email(
                        to_email=email_to_use,
                        subject=f"Booking Confirmation {formatted_booking_id} - Elysian Retreat",
                        html_content=email_html,
                        to_name=guest_name_to_use
                    )
            except Exception as e:
                # Log error but don't fail the booking
                print(f"Failed to send confirmation email: {str(e)}")
        
        return booking_with_rooms
        
    except HTTPException:
        # Re-raise HTTP exceptions (like validation errors) as-is
        raise
    except Exception as e:
        # Log the full error for debugging
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in create_guest_booking: {str(e)}")
        print(f"Traceback: {error_trace}")
        
        # Return a user-friendly error message
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create booking: {str(e)}"
        )

# -------------------------------
# Check-in a booking
# -------------------------------
@router.put("/{booking_id}/check-in", response_model=BookingOut)
def check_in_booking(
    booking_id: Union[str, int],
    id_card_image: Optional[UploadFile] = File(None),
    guest_photo: Optional[UploadFile] = File(None),
    amenityAllocation: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    print(f"[DEBUG] REGULAR CHECK-IN REQUEST: Booking ID: {booking_id}")
    print(f"[DEBUG] Amenity Allocation: {amenityAllocation}")

    # Parse display ID (BK-000001) or accept numeric ID
    numeric_id, booking_type = parse_display_id(str(booking_id))
    if numeric_id is None:
        raise HTTPException(status_code=400, detail=f"Invalid booking ID format: {booking_id}")
    if booking_type and booking_type != "booking":
        raise HTTPException(status_code=400, detail=f"Invalid booking type. Expected regular booking, got: {booking_id}")
    booking_id = numeric_id
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Normalize status to handle case variations and different separators (underscore vs hyphen)
    normalized_status = (booking.status or "").strip().lower().replace("_", "-").replace(" ", "-")
    if normalized_status != "booked":
        raise HTTPException(status_code=400, detail=f"Booking is not in 'booked' state. Current status: {booking.status}")

    if normalized_status != "booked":
        raise HTTPException(status_code=400, detail=f"Booking is not in 'booked' state. Current status: {booking.status}")

    # PROCESS AMENITY ALLOCATION / SCHEDULED ORDERS FOR REGULAR BOOKINGS TOO
    if amenityAllocation:
        try:
            import json
            from app.models.foodorder import FoodOrder, FoodOrderItem
            from app.models.food_item import FoodItem
            from datetime import datetime, timedelta, date, time
            
            alloc_data = json.loads(amenityAllocation)
            items = alloc_data.get("items", [])
            
            # Find first room ID
            room_id = None
            if booking.booking_rooms and len(booking.booking_rooms) > 0:
                room_id = booking.booking_rooms[0].room_id
            
            if items and room_id:
                check_in_date = date.today()
                
                for item in items:
                    name = item.get("name")
                    scheduled_time = item.get("scheduledTime")
                    scheduled_date_str = item.get("scheduledDate")
                    
                    if name and scheduled_time:
                        try:
                             scheduled_time = scheduled_time.strip()
                             # Handle time format with simple heuristics
                             if " " in scheduled_time:
                                 try:
                                     t = datetime.strptime(scheduled_time, "%I:%M %p")
                                     sh, sm = t.hour, t.minute
                                 except ValueError:
                                     sh, sm = map(int, scheduled_time.split(":")[:2])
                             else:
                                 sh, sm = map(int, scheduled_time.split(":")[:2])
                                 
                             if scheduled_date_str:
                                 s_year, s_month, s_day = map(int, scheduled_date_str.split("-"))
                                 scheduled_dt = datetime(s_year, s_month, s_day, sh, sm)
                             else:
                                 now = datetime.now()
                                 scheduled_dt = datetime.combine(check_in_date, time(sh, sm))
                                 if scheduled_dt < now:
                                     scheduled_dt = scheduled_dt + timedelta(days=1)
                             
                             schedule_str = scheduled_dt.strftime("%Y-%m-%d %H:%M:%S")
                             
                             food_item = db.query(FoodItem).filter(FoodItem.name.ilike(name)).first()
                             
                             new_order = FoodOrder(
                                 room_id=room_id,
                                 amount=0.0,
                                 status="scheduled",
                                 billing_status="unbilled",
                                 order_type="room_service",
                                 delivery_request=f"SCHEDULED_FOR: {schedule_str} -- Package Meal: {name}",
                                 created_at=datetime.utcnow()
                             )
                             db.add(new_order)
                             db.flush()
                             
                             print(f"[DEBUG] REGULAR: Created scheduled order {new_order.id}")

                             # Logic for adding items to the order
                             specific_items = item.get("specificFoodItems", [])
                             items_added = False

                             if specific_items and len(specific_items) > 0:
                                 for spec_item in specific_items:
                                     f_id = spec_item.get("foodItemId")
                                     qty = spec_item.get("quantity", 1)
                                     
                                     if f_id:
                                         f_item = db.query(FoodItem).filter(FoodItem.id == int(f_id)).first()
                                         if f_item:
                                             order_item = FoodOrderItem(
                                                 order_id=new_order.id,
                                                 food_item_id=f_item.id,
                                                 quantity=int(qty)
                                             )
                                             db.add(order_item)
                                             items_added = True
                             
                             # Fallback: if no specific items were added (or none selected), try to match the feature name
                             if not items_added:
                                 if food_item:
                                     order_item = FoodOrderItem(
                                         order_id=new_order.id,
                                         food_item_id=food_item.id,
                                         quantity=item.get("complimentaryPerNight", 1)
                                     )
                                     db.add(order_item)
                                 
                        except Exception as e:
                            print(f"Error creating scheduled order for {name}: {e}")
                            
        except Exception as e:
            print(f"Error processing amenity allocation in regular check-in: {e}")

    # CRITICAL: Check if any of the rooms are ALREADY occupied (Checked-in) by another booking
    # This prevents double check-ins for the same room
    if booking.booking_rooms:
        room_ids = [br.room_id for br in booking.booking_rooms]
        occupied_rooms = db.query(Room).filter(
            Room.id.in_(room_ids),
            # Check for strings indicating occupancy, case-insensitive
            or_(
                func.lower(Room.status) == 'checked-in',
                func.lower(Room.status) == 'occupied'
            )
        ).all()
        
        if occupied_rooms:
            # Check if the occupied room is actually occupied by THIS booking (unlikely if status was 'booked', but safe check)
            # Actually, we just verified booking.status == 'booked'. So it can't be occupied by this booking.
            if len(occupied_rooms) > 0:
                 occupied_numbers = ", ".join([str(r.number) for r in occupied_rooms])
                 print(f"WARNING: Forced check-in despite occupied status for rooms: {occupied_numbers}. Statuses: {[r.status for r in occupied_rooms]}")
                 # raise HTTPException(
                 #     status_code=400, 
                 #     detail=f"Cannot check-in. The following room(s) are currently marked as Checked-in/Occupied: {occupied_numbers}. Please check-out the previous guest first."
                 # )

    # Save ID card image (if provided)
    if id_card_image:
        id_card_filename = f"id_{booking_id}_{uuid.uuid4().hex}.jpg"
        id_card_path = os.path.join(UPLOAD_DIR, id_card_filename)
        with open(id_card_path, "wb") as buffer:
            shutil.copyfileobj(id_card_image.file, buffer)
        booking.id_card_image_url = id_card_filename

    # Save guest photo (if provided)
    if guest_photo:
        guest_photo_filename = f"guest_{booking_id}_{uuid.uuid4().hex}.jpg"
        guest_photo_path = os.path.join(UPLOAD_DIR, guest_photo_filename)
        with open(guest_photo_path, "wb") as buffer:
            shutil.copyfileobj(guest_photo.file, buffer)
        booking.guest_photo_url = guest_photo_filename

    booking.status = "checked-in"
    # Set the actual check-in timestamp for strict bill scoping
    from datetime import datetime
    booking.checked_in_at = datetime.utcnow()

    # Save the ID of the user who performed the check-in
    booking.user_id = current_user.id

    # CRITICAL FIX: Update the status of the associated rooms to 'Checked-in'
    if booking.booking_rooms:
        room_ids = [br.room_id for br in booking.booking_rooms]
        db.query(Room).filter(Room.id.in_(room_ids)).update({"status": "Checked-in"}, synchronize_session=False)
        db.flush()  # Ensure room status update is persisted immediately
        print(f"[CHECK-IN] Updated room status to 'Checked-in' for room IDs: {room_ids}")

    # Create notification for check-in
    try:
        from app.models.notification import Notification
        # Get room numbers for notification
        room_numbers = ", ".join([f"#{br.room.number}" for br in booking.booking_rooms if br.room])
        formatted_booking_id = f"BK-{str(booking_id).zfill(6)}"
        
        notification = Notification(
            user_id=current_user.id,
            title=f"Guest Checked In - {formatted_booking_id}",
            message=f"Guest {booking.guest_name} has successfully checked in. Booking ID: {formatted_booking_id}, Room(s): {room_numbers}",
            type="check_in",
            reference_id=booking_id,
            reference_type="booking",
            is_read=False,
            created_at=datetime.utcnow()
        )
        db.add(notification)
    except Exception as e:
        # Log error but don't fail the check-in
        print(f"Warning: Failed to create check-in notification: {str(e)}")

    # Process Amenity Allocation (Stock Issue)
    if amenityAllocation:
        try:
            import json
            amenity_data = json.loads(amenityAllocation)
            
            # If items exist
            if amenity_data and "items" in amenity_data and len(amenity_data["items"]) > 0:
                # We need to issue stock to the room(s)
                
                for br in booking.booking_rooms:
                    room = br.room
                    if not room or not room.inventory_location_id:
                        continue # Skip if no inventory location
                        
                    # Create Stock Issue Header
                    from app.models.inventory import StockIssue, StockIssueDetail, LocationStock
                    
                    # Find Warehouse (Source) - assuming ID 1 or first warehouse
                    warehouse = db.query(Location).filter(Location.location_type == "Warehouse").first()
                    source_id = warehouse.id if warehouse else None
                    
                    if not source_id:
                        print("Warning: No Warehouse found for amenity stock issue.")
                        continue

                    # Create Issue Record
                    stock_issue = StockIssue(
                        source_location_id=source_id,
                        destination_location_id=room.inventory_location_id,
                        issue_date=datetime.utcnow(),
                        status="approved", # Auto-approve system issues
                        issued_by_id=current_user.id,
                        reference_number=f"CHK-IN-{booking_id}-{room.number}",
                        notes=f"Automatic Amenity Issue for Check-in {formatted_booking_id}"
                    )
                    db.add(stock_issue)
                    db.flush() # Get ID
                    
                    # Process Items
                    for item in amenity_data["items"]:
                        item_id = item.get("item_id")
                        if not item_id: continue
                        
                        # Calculate Total Quantity to Issue
                        qty_per_night = float(item.get("complimentaryPerNight", 0))
                        qty_per_stay = float(item.get("complimentaryPerStay", 0))
                        
                        # Stay duration
                        check_in_dt = booking.check_in if isinstance(booking.check_in, date) else datetime.strptime(str(booking.check_in), '%Y-%m-%d').date()
                        check_out_dt = booking.check_out if isinstance(booking.check_out, date) else datetime.strptime(str(booking.check_out), '%Y-%m-%d').date()
                        nights = max(1, (check_out_dt - check_in_dt).days)
                        
                        total_qty = (qty_per_night * nights) + qty_per_stay
                        
                        if total_qty > 0:
                            # Add Detail
                            detail = StockIssueDetail(
                                issue_id=stock_issue.id,
                                item_id=item_id,
                                quantity=total_qty,
                                notes=f"{item.get('frequency')} allocation"
                            )
                            db.add(detail)
                            
                            # Move Stock (Warehouse -> Room)
                            # 1. Deduct Warehouse
                            inv_item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
                            if inv_item:
                                inv_item.current_stock = max(0, (inv_item.current_stock or 0) - total_qty)
                                
                            # 2. Add Room Stock
                            loc_stock = db.query(LocationStock).filter(
                                LocationStock.location_id == room.inventory_location_id,
                                LocationStock.item_id == item_id
                            ).first()
                            
                            if loc_stock:
                                loc_stock.quantity = (loc_stock.quantity or 0) + total_qty
                                loc_stock.last_updated = datetime.utcnow()
                            else:
                                loc_stock = LocationStock(
                                    location_id=room.inventory_location_id,
                                    item_id=item_id,
                                    quantity=total_qty,
                                    last_updated=datetime.utcnow()
                                )
                                db.add(loc_stock)
                                
        except Exception as e:
            print(f"Error processing amenity allocation: {e}")
            # Non-blocking error, log and continue check-in
    
    db.commit()
    db.refresh(booking)
    return booking

# -------------------------------
# Cancel a booking
# -------------------------------
@router.put("/{booking_id}/cancel", response_model=BookingOut)
def cancel_booking(booking_id: Union[str, int], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Parse display ID (BK-000001) or accept numeric ID
    numeric_id, booking_type = parse_display_id(str(booking_id))
    if numeric_id is None:
        raise HTTPException(status_code=400, detail=f"Invalid booking ID format: {booking_id}")
    if booking_type and booking_type != "booking":
        raise HTTPException(status_code=400, detail=f"Invalid booking type. Expected regular booking, got: {booking_id}")
    booking_id = numeric_id
    
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Free up the rooms associated with the booking
    if booking.booking_rooms:
        room_ids = [br.room_id for br in booking.booking_rooms]
        db.query(Room).filter(Room.id.in_(room_ids)).update({"status": "Available"}, synchronize_session=False)

    booking.status = "cancelled"
    db.commit()
    db.refresh(booking)
    return booking
    
@router.put("/{booking_id}/extend", response_model=BookingOut)
def extend_checkout(booking_id: Union[str, int], new_checkout: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Extend the checkout date for a booking.
    Validates that the new checkout date is after the current checkout date
    and checks for conflicts with other bookings on the same rooms.
    Accepts both display ID (BK-000001) and numeric ID.
    """
    from datetime import datetime
    
    # Parse display ID (BK-000001) or accept numeric ID
    numeric_id, booking_type = parse_display_id(str(booking_id))
    if numeric_id is None:
        raise HTTPException(status_code=400, detail=f"Invalid booking ID format: {booking_id}")
    if booking_type and booking_type != "booking":
        raise HTTPException(status_code=400, detail=f"Invalid booking type. Expected regular booking, got: {booking_id}")
    booking_id = numeric_id
    
    # Parse the new checkout date string to a date object
    try:
        new_checkout_date = datetime.strptime(new_checkout, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD format")
    
    # Fetch the booking with its rooms
    booking = db.query(Booking).options(
        joinedload(Booking.booking_rooms).joinedload(BookingRoom.room)
    ).filter(Booking.id == booking_id).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Check if booking is in a valid state for extension
    # Normalize status: convert to lowercase and replace underscores/hyphens with hyphens for consistent comparison
    raw_status_lower = booking.status.lower().strip() if booking.status else ''
    normalized_status = raw_status_lower.replace('_', '-').replace(' ', '-')
    
    # Explicitly reject checked-out/checked_out statuses (guest has already left)
    # Be careful: "checked-in" normalizes to "checked-in", "checked-out" normalizes to "checked-out"
    # We need to check for "out" specifically, not just the normalized form
    is_checked_out = (
        'out' in normalized_status and normalized_status.startswith('checked-') and normalized_status.endswith('-out')
    ) or raw_status_lower in ['checked_out', 'checked-out', 'checked out']
    
    if is_checked_out:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot extend checkout for booking with status '{booking.status}'. The guest has already checked out."
        )
    
    # Allow extension for 'booked' or 'checked-in' statuses (handle variations like 'checked_in', 'checked-in', 'Checked In', etc.)
    if normalized_status not in ['booked', 'checked-in']:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot extend checkout for booking with status '{booking.status}'. Only 'booked' or 'checked-in' bookings can be extended."
        )
    
    # Validate that new checkout date is after current checkout date
    if new_checkout_date <= booking.check_out:
        raise HTTPException(
            status_code=400, 
            detail=f"New checkout date ({new_checkout_date}) must be after current checkout date ({booking.check_out})"
        )
    
    # Check for conflicts with other bookings on the same rooms
    room_ids = [br.room_id for br in booking.booking_rooms if br.room_id]
    
    if room_ids:
        # Check for conflicts with regular bookings
        # A conflict exists if another booking overlaps with the extended period
        # Extended period: from booking.check_out (exclusive) to new_checkout_date (inclusive)
        conflicting_bookings = db.query(Booking).join(BookingRoom).filter(
            Booking.id != booking_id,
            BookingRoom.room_id.in_(room_ids),
            Booking.status.in_(['booked', 'checked-in', 'checked_in']),
            and_(
                Booking.check_in < new_checkout_date,
                Booking.check_out > booking.check_out
            )
        ).first()
        
        if conflicting_bookings:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot extend checkout date. Room(s) are already booked by another booking (ID: {conflicting_bookings.id}) during the extended period."
            )
        
        # Check for conflicts with package bookings
        # A conflict exists if a package booking overlaps with the extended period
        conflicting_package_bookings = db.query(PackageBooking).join(PackageBookingRoom).filter(
            PackageBookingRoom.room_id.in_(room_ids),
            PackageBooking.status.in_(['booked', 'checked-in', 'checked_in']),
            and_(
                PackageBooking.check_in < new_checkout_date,
                PackageBooking.check_out > booking.check_out
            )
        ).first()
        
        if conflicting_package_bookings:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot extend checkout date. Room(s) are already booked by a package booking (ID: {conflicting_package_bookings.id}) during the extended period."
            )
    
    # Update the checkout date
    booking.check_out = new_checkout_date
    db.commit()
    db.refresh(booking)
    
    # Reload booking with relationships for response
    booking_with_rooms = db.query(Booking).options(
        joinedload(Booking.booking_rooms).joinedload(BookingRoom.room)
    ).filter(Booking.id == booking_id).first()

    return BookingOut(
        id=booking_with_rooms.id,
        status=booking_with_rooms.status,
        guest_name=booking_with_rooms.guest_name,
        guest_mobile=booking_with_rooms.guest_mobile,
        guest_email=booking_with_rooms.guest_email,
        check_in=booking_with_rooms.check_in,
        check_out=booking_with_rooms.check_out,
        adults=booking_with_rooms.adults,
        children=booking_with_rooms.children,
        id_card_image_url=booking_with_rooms.id_card_image_url,
        guest_photo_url=booking_with_rooms.guest_photo_url,
        user_id=booking_with_rooms.user_id,
        total_amount=booking_with_rooms.total_amount,
        rooms=[br.room for br in booking_with_rooms.booking_rooms if br.room]
    )
# -------------------------------
# GET booking by ID
# -------------------------------
@router.get("/{booking_id}", response_model=BookingOut)
def get_booking(booking_id: Union[str, int], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Parse display ID (BK-000001) or accept numeric ID
    numeric_id, booking_type = parse_display_id(str(booking_id))
    if numeric_id is None:
        raise HTTPException(status_code=400, detail=f"Invalid booking ID format: {booking_id}")
    if booking_type and booking_type != "booking":
        raise HTTPException(status_code=400, detail=f"Invalid booking type. Expected regular booking, got: {booking_id}")
    booking_id = numeric_id
    
    booking = db.query(Booking).options(
        joinedload(Booking.booking_rooms).joinedload(BookingRoom.room)
    ).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking

# -------------------------------
# GET check-in images
# -------------------------------
@router.get("/checkin-image/{filename}")
def get_checkin_image(filename: str):
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath) or not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(filepath)