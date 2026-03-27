from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from typing import List

from app.models.Package import Package, PackageImage, PackageBooking, PackageBookingRoom
from app.models.room import Room
from app.schemas.packages import PackageBookingCreate


# ------------------- Packages -------------------

def create_package(db: Session, title: str, description: str, price: float, image_urls: List[str], booking_type: str = "room_type", room_types: str = None):
    try:
        pkg = Package(
            title=title, 
            description=description, 
            price=price,
            booking_type=booking_type,
            room_types=room_types
        )
        db.add(pkg)
        db.commit()
        db.refresh(pkg)

        for url in image_urls:
            img = PackageImage(package_id=pkg.id, image_url=url)
            db.add(img)
        db.commit()
        db.refresh(pkg)
        return pkg
    except Exception as e:
        db.rollback()
        import traceback
        error_detail = f"Database error in create_package: {str(e)}\n{traceback.format_exc()}"
        print(f"ERROR: {error_detail}")
        import sys
        sys.stderr.write(f"ERROR in create_package: {error_detail}\n")
        raise HTTPException(status_code=500, detail=f"Failed to create package: {str(e)}")





def delete_package(db: Session, package_id: int):
    pkg = db.query(Package).filter(Package.id == package_id).first()
    if not pkg:
        return False
    db.delete(pkg)
    db.commit()
    return True


# ------------------- Package Bookings -------------------
def get_package_bookings(db: Session):
    return (
        db.query(PackageBooking)
        .join(PackageBooking.package)  # Use an inner join to filter out bookings with no package
        .options(joinedload(PackageBooking.rooms).joinedload(PackageBookingRoom.room))
    ).all()

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

def book_package(db: Session, booking: PackageBookingCreate):
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
    
    # Check for an existing package booking to reuse guest details for consistency
    # Only check if we have at least email or mobile
    existing_booking = None
    if guest_email or guest_mobile:
        existing_query = db.query(PackageBooking)
        
        # Add email filter if normalized email exists
        if guest_email:
            existing_query = existing_query.filter(PackageBooking.guest_email == guest_email)
        
        # Add mobile filter if normalized mobile exists
        if guest_mobile:
            existing_query = existing_query.filter(PackageBooking.guest_mobile == guest_mobile)
        
        existing_booking = existing_query.order_by(PackageBooking.id.desc()).first()

    guest_name_to_use = booking.guest_name or "Guest User"
    if existing_booking:
        # If a guest with the same email and mobile exists, use their established name
        guest_name_to_use = existing_booking.guest_name

    # Validate room capacity for adults and children separately (skip for whole_property packages)
    selected_package = db.query(Package).filter(Package.id == booking.package_id).first()
    if not selected_package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    is_whole_property = selected_package.booking_type == 'whole_property'
    
    if not is_whole_property and booking.room_ids:
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

    # CRITICAL FIX: Check for conflicts BEFORE creating the booking
    # This prevents invalid bookings from being created in the database
    for room_id in booking.room_ids:
        # Check for conflicts with package bookings (simplified overlap check: start1 < end2 AND start2 < end1)
        package_conflict = (
            db.query(PackageBookingRoom)
            .join(PackageBooking)
            .filter(
                PackageBookingRoom.room_id == room_id,
                PackageBooking.status.in_(["booked", "checked-in", "checked_in"]),  # Only check for active bookings
                PackageBooking.check_in < booking.check_out,
                PackageBooking.check_out > booking.check_in
            )
            .first()
        )

        # Check for conflicts with regular bookings (simplified overlap check: start1 < end2 AND start2 < end1)
        from app.models.booking import Booking, BookingRoom
        regular_conflict = (
            db.query(BookingRoom)
            .join(Booking)
            .filter(
                BookingRoom.room_id == room_id,
                Booking.status.in_(["booked", "checked-in", "checked_in"]),  # Only check for active bookings
                Booking.check_in < booking.check_out,
                Booking.check_out > booking.check_in
            )
            .first()
        )

        if package_conflict or regular_conflict:
            room = db.query(Room).filter(Room.id == room_id).first()
            raise HTTPException(status_code=400, detail=f"Room {room.number if room else room_id} is not available for the selected dates.")

    # All conflict checks passed - now create the booking
    db_booking = PackageBooking(
        package_id=booking.package_id,
        check_in=booking.check_in,
        check_out=booking.check_out,
        guest_name=guest_name_to_use,
        guest_email=guest_email or booking.guest_email or None,  # Use normalized email or original, fallback to None
        guest_mobile=guest_mobile or booking.guest_mobile or None,  # Use normalized mobile or original, fallback to None
        adults=booking.adults,
        children=booking.children,
        status="booked",
        user_id=guest_user_id,  # Link booking to guest user
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    # Assign multiple rooms (conflicts already checked, safe to proceed)
    for room_id in booking.room_ids:
        # Update the room's status to 'Booked'
        room_to_update = db.query(Room).filter(Room.id == room_id).first()
        if room_to_update:
            room_to_update.status = "Booked"

        db_room_link = PackageBookingRoom(package_booking_id=db_booking.id, room_id=room_id)
        db.add(db_room_link)

    db.commit()

    # Reload with rooms + room details
    booking_with_rooms = (
        db.query(PackageBooking)
        .options(joinedload(PackageBooking.rooms).joinedload(PackageBookingRoom.room))
        .filter(PackageBooking.id == db_booking.id)
        .first()
    )
    return booking_with_rooms





def delete_package_booking(db: Session, booking_id: int):
    booking = db.query(PackageBooking).filter(PackageBooking.id == booking_id).first()
    if not booking:
        return False

    booking.status = "cancelled"

    for link in booking.rooms:
        room_to_update = db.query(Room).filter(Room.id == link.room_id).first()
        if room_to_update:
            room_to_update.status = "Available"

    db.commit()
    db.refresh(booking)
    return True
def get_packages(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Package).offset(skip).limit(limit).all()


def get_package(db: Session, package_id: int):
    return db.query(Package).filter(Package.id == package_id).first()