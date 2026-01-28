from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload
from typing import List, Union
import os
from app.models.user import User
from app.models.room import Room
from app.models.Package import Package, PackageBooking, PackageBookingRoom
from app.utils.auth import get_db, get_current_user
from app.utils.booking_id import parse_display_id
from app.schemas.packages import PackageBookingCreate, PackageOut, PackageBookingOut
from fastapi.responses import FileResponse
from app.curd import packages as crud_package
import shutil
import uuid

router = APIRouter(prefix="/packages", tags=["Packages"])

UPLOAD_DIR = "uploads/packages"
CHECKIN_UPLOAD_DIR = "uploads/checkin_proofs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHECKIN_UPLOAD_DIR, exist_ok=True)


# ------------------- Packages -------------------

@router.post("", response_model=PackageOut)
async def create_package_api(
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    booking_type: str = Form("room_type"),  # "whole_property" or "room_type"
    room_types: str = Form(None),  # Comma-separated list of room types
    theme: str = Form(None),
    default_adults: int = Form(2),
    default_children: int = Form(0),
    max_stay_days: int = Form(None),
    food_included: str = Form(None),
    food_timing: str = Form(None),
    complimentary: str = Form(None),
    images: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Validate booking_type
        if booking_type not in ["whole_property", "room_type"]:
            raise HTTPException(status_code=400, detail="booking_type must be either 'whole_property' or 'room_type'")
        
        # If booking_type is room_type, room_types must be provided
        if booking_type == "room_type" and not room_types:
            raise HTTPException(status_code=400, detail="room_types is required when booking_type is 'room_type'")
        
        # If booking_type is whole_property, room_types should be empty
        if booking_type == "whole_property":
            room_types = None
        
        image_urls = []
        try:
            for img in images:
                # Generate unique filename - handle case where filename might be None
                original_filename = img.filename if img.filename else "image.jpg"
                filename = f"pkg_{uuid.uuid4().hex}_{original_filename}"
                file_path = os.path.join(UPLOAD_DIR, filename)
                
                # Use async file operations for better performance with large files
                try:
                    # Read file content asynchronously
                    contents = await img.read()
                    # Write to disk
                    with open(file_path, "wb") as buffer:
                        buffer.write(contents)
                except (AttributeError, TypeError):
                    # Fallback to synchronous if async methods not available
                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(img.file, buffer)
                
                # Store with leading slash for proper URL construction
                normalized_path = file_path.replace('\\', '/')
                image_urls.append(f"/{normalized_path}")
        except Exception as img_error:
            import traceback
            error_detail = f"Failed to save package images: {str(img_error)}\n{traceback.format_exc()}"
            print(f"ERROR: {error_detail}")
            import sys
            sys.stderr.write(f"ERROR in create_package_api (image upload): {error_detail}\n")
            raise HTTPException(status_code=500, detail=f"Failed to upload images: {str(img_error)}")

        try:
            return crud_package.create_package(db, title, description, price, image_urls, booking_type, room_types, theme, default_adults, default_children, max_stay_days, food_included, food_timing, complimentary)
        except Exception as db_error:
            import traceback
            error_detail = f"Failed to create package in database: {str(db_error)}\n{traceback.format_exc()}"
            print(f"ERROR: {error_detail}")
            import sys
            sys.stderr.write(f"ERROR in create_package_api (database): {error_detail}\n")
            # Clean up uploaded images if package creation fails
            for img_url in image_urls:
                try:
                    # Remove leading slash to get actual file path
                    file_path = img_url.lstrip('/')
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as cleanup_error:
                    print(f"Warning: Failed to cleanup image {img_url}: {str(cleanup_error)}")
            raise HTTPException(status_code=500, detail=f"Failed to create package: {str(db_error)}")
    except HTTPException:
        # Re-raise HTTP exceptions (like validation errors) as-is
        raise
    except Exception as e:
        import traceback
        error_detail = f"Unexpected error in create_package_api: {str(e)}\n{traceback.format_exc()}"
        print(f"ERROR: {error_detail}")
        import sys
        sys.stderr.write(f"ERROR in create_package_api: {error_detail}\n")
        raise HTTPException(status_code=500, detail=f"Failed to create package: {str(e)}")


@router.post("/", response_model=PackageOut)  # Handle trailing slash
async def create_package_api_slash(
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    booking_type: str = Form("room_type"),
    room_types: str = Form(None),
    theme: str = Form(None),
    default_adults: int = Form(2),
    default_children: int = Form(0),
    max_stay_days: int = Form(None),
    food_included: str = Form(None),
    food_timing: str = Form(None),
    complimentary: str = Form(None),
    images: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Handle POST /packages/ with trailing slash"""
    try:
        # Validate booking_type
        if booking_type not in ["whole_property", "room_type"]:
            raise HTTPException(status_code=400, detail="booking_type must be either 'whole_property' or 'room_type'")
        
        # If booking_type is room_type, room_types must be provided
        if booking_type == "room_type" and not room_types:
            raise HTTPException(status_code=400, detail="room_types is required when booking_type is 'room_type'")
        
        # If booking_type is whole_property, room_types should be empty
        if booking_type == "whole_property":
            room_types = None
        
        image_urls = []
        try:
            for img in images:
                # Generate unique filename - handle case where filename might be None
                original_filename = img.filename if img.filename else "image.jpg"
                filename = f"pkg_{uuid.uuid4().hex}_{original_filename}"
                file_path = os.path.join(UPLOAD_DIR, filename)
                
                # Use async file operations for better performance with large files
                try:
                    # Read file content asynchronously
                    contents = await img.read()
                    # Write to disk
                    with open(file_path, "wb") as buffer:
                        buffer.write(contents)
                except (AttributeError, TypeError):
                    # Fallback to synchronous if async methods not available
                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(img.file, buffer)
                
                # Store with leading slash for proper URL construction
                normalized_path = file_path.replace('\\', '/')
                image_urls.append(f"/{normalized_path}")
        except Exception as img_error:
            import traceback
            error_detail = f"Failed to save package images: {str(img_error)}\n{traceback.format_exc()}"
            print(f"ERROR: {error_detail}")
            import sys
            sys.stderr.write(f"ERROR in create_package_api_slash (image upload): {error_detail}\n")
            raise HTTPException(status_code=500, detail=f"Failed to upload images: {str(img_error)}")

        try:
            return crud_package.create_package(db, title, description, price, image_urls, booking_type, room_types, theme, default_adults, default_children, max_stay_days, food_included, food_timing, complimentary)
        except Exception as db_error:
            import traceback
            error_detail = f"Failed to create package in database: {str(db_error)}\n{traceback.format_exc()}"
            print(f"ERROR: {error_detail}")
            import sys
            sys.stderr.write(f"ERROR in create_package_api_slash (database): {error_detail}\n")
            # Clean up uploaded images if package creation fails
            for img_url in image_urls:
                try:
                    # Remove leading slash to get actual file path
                    file_path = img_url.lstrip('/')
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as cleanup_error:
                    print(f"Warning: Failed to cleanup image {img_url}: {str(cleanup_error)}")
            raise HTTPException(status_code=500, detail=f"Failed to create package: {str(db_error)}")
    except HTTPException:
        # Re-raise HTTP exceptions (like validation errors) as-is
        raise
    except Exception as e:
        import traceback
        error_detail = f"Unexpected error in create_package_api_slash: {str(e)}\n{traceback.format_exc()}"
        print(f"ERROR: {error_detail}")
        import sys
        sys.stderr.write(f"ERROR in create_package_api_slash: {error_detail}\n")
        raise HTTPException(status_code=500, detail=f"Failed to create package: {str(e)}")


@router.put("/{package_id}", response_model=PackageOut)
async def update_package_api(
    package_id: int,
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    booking_type: str = Form("room_type"),  # "whole_property" or "room_type"
    room_types: str = Form(None),  # Comma-separated list of room types
    theme: str = Form(None),
    default_adults: int = Form(2),
    default_children: int = Form(0),
    max_stay_days: int = Form(None),
    food_included: str = Form(None),
    food_timing: str = Form(None),
    complimentary: str = Form(None),
    images: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate booking_type
    if booking_type not in ["whole_property", "room_type"]:
        raise HTTPException(status_code=400, detail="booking_type must be either 'whole_property' or 'room_type'")
    
    # If booking_type is room_type, room_types must be provided
    if booking_type == "room_type" and not room_types:
        raise HTTPException(status_code=400, detail="room_types is required when booking_type is 'room_type'")
    
    # If booking_type is whole_property, room_types should be empty
    if booking_type == "whole_property":
        room_types = None
    
    # Get existing package
    package = db.query(Package).filter(Package.id == package_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")
    
    # Update package fields
    package.title = title
    package.description = description
    package.price = price
    package.booking_type = booking_type
    package.room_types = room_types
    package.theme = theme
    package.complimentary = complimentary
    package.default_adults = default_adults
    package.default_children = default_children
    package.max_stay_days = max_stay_days
    package.food_included = food_included
    package.food_timing = food_timing
    package.status = status
    
    # Add new images if provided
    if images:
        image_urls = []
        for img in images:
            # Generate unique filename
            filename = f"pkg_{uuid.uuid4().hex}_{img.filename}"
            file_path = os.path.join(UPLOAD_DIR, filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(img.file, buffer)
            # Store with leading slash for proper URL construction
            normalized_path = file_path.replace('\\', '/')
            image_urls.append(f"/{normalized_path}")
        
        # Add new images to existing ones
        for url in image_urls:
            from app.models.Package import PackageImage
            img = PackageImage(package_id=package.id, image_url=url)
            db.add(img)
    
    db.commit()
    db.refresh(package)
    return package


@router.delete("/{package_id}")
def delete_package_api(package_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    success = crud_package.delete_package(db, package_id)
    return {"deleted": success}


# ------------------- Package Bookings -------------------

@router.post("/book", response_model=PackageBookingOut)
def book_package_api(
    booking: PackageBookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = crud_package.book_package(db, booking)
    
    # Calculate booking charges and send confirmation email if email address is provided
    if booking.guest_email and result:
        try:
            from app.utils.email import send_email, create_booking_confirmation_email
            from datetime import datetime, date
            
            # Get package details
            package = db.query(Package).filter(Package.id == booking.package_id).first()
            
            # Calculate stay duration
            check_in_date = result.check_in if isinstance(result.check_in, date) else datetime.strptime(str(result.check_in), '%Y-%m-%d').date()
            check_out_date = result.check_out if isinstance(result.check_out, date) else datetime.strptime(str(result.check_out), '%Y-%m-%d').date()
            stay_nights = max(1, (check_out_date - check_in_date).days)
            
            # Calculate package charges (package price per night per room)
            package_price = package.price if package else 0
            package_charges = package_price * stay_nights * len(booking.room_ids) if booking.room_ids else package_price * stay_nights
            
            # Get room details with prices
            rooms_data = []
            for pbr in result.rooms:
                if pbr.room:
                    rooms_data.append({
                        'number': pbr.room.number,
                        'type': pbr.room.type or 'Standard',
                        'price': pbr.room.price or 0
                    })
            
            # Format booking ID (PK-000001)
            formatted_booking_id = f"PK-{str(result.id).zfill(6)}"
            
            email_html = create_booking_confirmation_email(
                guest_name=result.guest_name,
                booking_id=result.id,
                booking_type='package',
                check_in=str(result.check_in),
                check_out=str(result.check_out),
                rooms=rooms_data,
                total_amount=package_charges,
                package_name=package.title if package else None,
                guests={'adults': booking.adults, 'children': booking.children},
                guest_mobile=booking.guest_mobile,
                package_charges=package_charges,
                stay_nights=stay_nights
            )
            
            send_email(
                to_email=booking.guest_email,
                subject=f"Package Booking Confirmation {formatted_booking_id} - Elysian Retreat",
                html_content=email_html,
                to_name=result.guest_name
            )
        except Exception as e:
            # Log error but don't fail the booking
            print(f"Failed to send confirmation email: {str(e)}")
    
    return result

@router.post("/book/guest", response_model=PackageBookingOut, summary="Book a package as a guest")
def book_package_guest_api(
    booking: PackageBookingCreate,
    db: Session = Depends(get_db)
):
    """
    Public endpoint for guests to book a package without authentication.
    """
    try:
        result = crud_package.book_package(db, booking)
        
        # Calculate booking charges and send confirmation email if email address is provided
        if result:
            # Normalize email for sending
            guest_email = None
            try:
                if booking.guest_email:
                    guest_email = booking.guest_email.strip() if isinstance(booking.guest_email, str) and booking.guest_email.strip() else None
            except (AttributeError, TypeError):
                pass
            
            if guest_email:
                try:
                    from app.utils.email import send_email, create_booking_confirmation_email
                    from datetime import datetime, date
                    
                    # Get package details
                    package = db.query(Package).filter(Package.id == booking.package_id).first()
                    
                    # Calculate stay duration
                    check_in_date = result.check_in if isinstance(result.check_in, date) else datetime.strptime(str(result.check_in), '%Y-%m-%d').date()
                    check_out_date = result.check_out if isinstance(result.check_out, date) else datetime.strptime(str(result.check_out), '%Y-%m-%d').date()
                    stay_nights = max(1, (check_out_date - check_in_date).days)
                    
                    # Calculate package charges (package price per night per room)
                    package_price = package.price if package else 0
                    package_charges = package_price * stay_nights * len(booking.room_ids) if booking.room_ids else package_price * stay_nights
                    
                    # Get room details with prices
                    rooms_data = []
                    for pbr in result.rooms:
                        if pbr.room:
                            rooms_data.append({
                                'number': pbr.room.number,
                                'type': pbr.room.type or 'Standard',
                                'price': pbr.room.price or 0
                            })
                    
                    # Format booking ID (PK-000001)
                    formatted_booking_id = f"PK-{str(result.id).zfill(6)}"
                    
                    email_html = create_booking_confirmation_email(
                        guest_name=result.guest_name,
                        booking_id=result.id,
                        booking_type='package',
                        check_in=str(result.check_in),
                        check_out=str(result.check_out),
                        rooms=rooms_data,
                        total_amount=package_charges,
                        package_name=package.title if package else None,
                        guests={'adults': booking.adults, 'children': booking.children},
                        guest_mobile=booking.guest_mobile,
                        package_charges=package_charges,
                        stay_nights=stay_nights
                    )
                    
                    send_email(
                        to_email=guest_email,
                        subject=f"Package Booking Confirmation {formatted_booking_id} - Elysian Retreat",
                        html_content=email_html,
                        to_name=result.guest_name
                    )
                except Exception as e:
                    # Log error but don't fail the booking
                    print(f"Failed to send confirmation email: {str(e)}")
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions (like validation errors) as-is
        raise
    except Exception as e:
        # Log the full error for debugging
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in book_package_guest_api: {str(e)}")
        print(f"Traceback: {error_trace}")
        
        # Return a user-friendly error message
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create package booking: {str(e)}"
        )

@router.get("/bookingsall", response_model=List[PackageBookingOut])
def get_bookings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), skip: int = 0, limit: int = 20):
    try:
        # Optimized for low network - reduced to 50
        if limit > 50:
            limit = 50
        if limit < 1:
            limit = 20
        
        # Simplified query - removed nested eager loading to prevent hangs
        # It's possible for a package to be deleted, leaving an orphaned booking.
        # We must filter to only include bookings that still have a valid package_id.
        result = db.query(PackageBooking).options(
            joinedload(PackageBooking.package)
            # Removed nested room loading to reduce query complexity
        ).filter(PackageBooking.package_id.is_not(None)).offset(skip).limit(limit).all()
        
        # Fallback: Calculate total amount if 0 (for legacy data)
        for booking in result:
            if (not booking.total_amount or booking.total_amount == 0) and booking.check_in and booking.check_out and booking.package:
                try:
                    from datetime import datetime, date
                    d_in = booking.check_in
                    d_out = booking.check_out
                    
                    if isinstance(d_in, str):
                        d_in = datetime.strptime(d_in, '%Y-%m-%d').date()
                    if isinstance(d_out, str):
                        d_out = datetime.strptime(d_out, '%Y-%m-%d').date()
                        
                    stay_days = (d_out - d_in).days
                    stay_nights = max(1, stay_days)
                    # For packages, price is per unit (usually room). Count rooms if available, else 1.
                    # We need to access rooms relationship if loaded, or assume 1 if not.
                    # Warning: rooms might not be eager loaded here based on lines above.
                    # But checking len(booking.rooms) might trigger lazy load if not detached.
                    num_rooms = len(booking.rooms) if booking.rooms else 1
                    
                    calc_amount = booking.package.price * stay_nights * num_rooms
                    
                    if calc_amount > 0:
                         booking.total_amount = calc_amount
                         # Self-healing
                         try:
                             from sqlalchemy import update
                             stmt = update(PackageBooking).where(PackageBooking.id == booking.id).values(total_amount=calc_amount)
                             db.execute(stmt)
                             db.commit()
                             print(f"Self-healed Package Booking {booking.id} total_amount to {calc_amount}")
                         except Exception as db_e:
                             print(f"Failed to update healed package amount: {db_e}")
                             db.rollback()

                except Exception as e:
                    print(f"Error patching total_amount for package {booking.id}: {e}")
                    pass

        return result if result is not None else []
    except Exception as e:
        import traceback
        error_detail = f"Failed to fetch package bookings: {str(e)}\n{traceback.format_exc()}"
        print(f"ERROR: {error_detail}")
        import sys
        sys.stderr.write(f"ERROR in /packages/bookingsall: {error_detail}\n")
        # Return empty list to prevent frontend breakage
        print(f"Unexpected error in package bookings endpoint, returning empty list: {str(e)}")
        return []


def _list_packages_impl(db: Session, skip: int = 0, limit: int = 20, status: str = None):
    """Helper function for list_packages"""
    try:
        # Optimized for low network - reduced to 50
        if limit > 50:
            limit = 50
        if limit < 1:
            limit = 20
        
        # Query directly in the endpoint to apply pagination and filtering
        query = db.query(Package)
        
        if status:
            query = query.filter(Package.status == status)
            
        result = query.offset(skip).limit(limit).all()
        return result if result is not None else []
    except Exception as e:
        import traceback
        error_detail = f"Failed to fetch packages: {str(e)}\n{traceback.format_exc()}"
        print(f"ERROR: {error_detail}")
        import sys
        sys.stderr.write(f"ERROR in /packages: {error_detail}\n")
        # Return empty list to prevent frontend breakage
        print(f"Unexpected error in packages endpoint, returning empty list: {str(e)}")
        return []

@router.get("", response_model=List[PackageOut])
def list_packages(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), skip: int = 0, limit: int = 20, status: str = None):
    return _list_packages_impl(db, skip, limit, status)

@router.get("/", response_model=List[PackageOut])  # Handle trailing slash
def list_packages_slash(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), skip: int = 0, limit: int = 20, status: str = None):
    return _list_packages_impl(db, skip, limit, status)


@router.get("/{package_id}", response_model=PackageOut)
def get_package_api(package_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud_package.get_package(db, package_id)


@router.delete("/booking/{booking_id}")
def delete_package_booking_api(booking_id: Union[str, int], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Parse display ID (PK-000001) or accept numeric ID
    numeric_id, booking_type = parse_display_id(str(booking_id))
    if numeric_id is None:
        raise HTTPException(status_code=400, detail=f"Invalid booking ID format: {booking_id}")
    if booking_type and booking_type != "package":
        raise HTTPException(status_code=400, detail=f"Invalid booking type. Expected package booking, got: {booking_id}")
    booking_id = numeric_id
    
    success = crud_package.delete_package_booking(db, booking_id)
    if not success:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"deleted": success}

# ------------------- Cancel a package booking -------------------
@router.put("/booking/{booking_id}/cancel", response_model=PackageBookingOut)
def cancel_package_booking(booking_id: Union[str, int], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Parse display ID (PK-000001) or accept numeric ID
    numeric_id, booking_type = parse_display_id(str(booking_id))
    if numeric_id is None:
        raise HTTPException(status_code=400, detail=f"Invalid booking ID format: {booking_id}")
    if booking_type and booking_type != "package":
        raise HTTPException(status_code=400, detail=f"Invalid booking type. Expected package booking, got: {booking_id}")
    booking_id = numeric_id
    
    booking = db.query(PackageBooking).filter(PackageBooking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Package booking not found")

    # Free rooms back to Available
    if booking.rooms:
        room_ids = [br.room_id for br in booking.rooms]
        db.query(Room).filter(Room.id.in_(room_ids)).update({"status": "Available"}, synchronize_session=False)

    booking.status = "cancelled"
    db.commit()
    db.refresh(booking)
    return booking

@router.put("/booking/{booking_id}/extend", response_model=PackageBookingOut)
def extend_package_booking_checkout(booking_id: Union[str, int], new_checkout: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Extend the checkout date for a package booking.
    Validates that the new checkout date is after the current checkout date
    and checks for conflicts with other bookings on the same rooms.
    Accepts both display ID (PK-000001) and numeric ID.
    """
    from datetime import datetime
    from sqlalchemy import and_, or_
    
    # Parse display ID (PK-000001) or accept numeric ID
    numeric_id, booking_type = parse_display_id(str(booking_id))
    if numeric_id is None:
        raise HTTPException(status_code=400, detail=f"Invalid booking ID format: {booking_id}")
    if booking_type and booking_type != "package":
        raise HTTPException(status_code=400, detail=f"Invalid booking type. Expected package booking, got: {booking_id}")
    booking_id = numeric_id
    
    # Parse the new checkout date string to a date object
    try:
        new_checkout_date = datetime.strptime(new_checkout, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD format")
    
    # Fetch the package booking with its rooms
    booking = db.query(PackageBooking).options(
        joinedload(PackageBooking.rooms).joinedload(PackageBookingRoom.room)
    ).filter(PackageBooking.id == booking_id).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Package booking not found")
    
    # IMPORTANT: Refresh the booking from database to get the latest status
    # This ensures we have the most current status, not a stale cached value
    db.refresh(booking)
    
    # Check if booking is in a valid state for extension
    # Normalize status: convert to lowercase and replace underscores/hyphens with hyphens for consistent comparison
    if not booking.status:
        raise HTTPException(
            status_code=400, 
            detail="Booking status is missing. Cannot extend checkout."
        )
    
    # Normalize status: handle variations like "booked", "Booked", "BOOKED", "checked-in", "checked_in", "checked-out", "checked_out"
    raw_status_lower = booking.status.lower().strip() if booking.status else ''
    # Replace underscores and spaces with hyphens, but be careful not to break "booked"
    normalized_status = raw_status_lower.replace('_', '-').replace(' ', '-')
    
    # Debug: Print the actual status values for troubleshooting
    print(f"[DEBUG] Extend package booking - ID: {booking_id}")
    print(f"[DEBUG]   Guest: {booking.guest_name}")
    print(f"[DEBUG]   Original status from DB: '{booking.status}'")
    print(f"[DEBUG]   Raw lower: '{raw_status_lower}'")
    print(f"[DEBUG]   Normalized: '{normalized_status}'")
    print(f"[DEBUG]   Check-in: {booking.check_in}, Check-out: {booking.check_out}")
    
    # First, check if it's explicitly "booked" - this should always be allowed and skip all other checks
    is_booked = normalized_status == 'booked' or raw_status_lower == 'booked'
    
    if is_booked:
        # "booked" status is always valid for extension - skip all other checks
        print(f"[DEBUG]   Status is 'booked' - allowing extension without further checks")
        # Continue to date validation and conflict checks below
    else:
        # For non-"booked" statuses, check if it's checked-out
        # Check if it's checked-out (must end with "-out" or be exactly "checked_out")
        # This ensures "checked-in" is NOT matched
        # Be very specific: only match if it explicitly contains "checked" and "out"
        is_checked_out = False
        if normalized_status == 'checked-out' or raw_status_lower in ['checked_out', 'checked-out', 'checked out']:
            is_checked_out = True
        elif normalized_status.startswith('checked-') and normalized_status.endswith('-out'):
            is_checked_out = True
        
        # Check if it's a valid status for extension (checked-in)
        is_valid_for_extension = (
            normalized_status == 'checked-in' or
            raw_status_lower in ['checked_in', 'checked-in', 'checked in']
        )
        
        print(f"[DEBUG]   Is valid for extension: {is_valid_for_extension}")
        print(f"[DEBUG]   Is checked out: {is_checked_out}")
        print(f"[DEBUG]   Has check-in images: id_card={bool(booking.id_card_image_url)}, guest_photo={bool(booking.guest_photo_url)}")
        
        # Special case: If status is "checked_out" but has check-in images, it might be a data inconsistency
        # Also check if check-out date is in the future (guest is still checked in)
        from datetime import date
        has_checkin_images = bool(booking.id_card_image_url) or bool(booking.guest_photo_url)
        today = date.today()
        checkout_is_future = booking.check_out >= today
        
        # If status says "checked_out" but:
        # 1. Has check-in images (guest was checked in), OR
        # 2. Check-out date is today or in the future (guest should still be checked in)
        # Then treat as checked-in for extension purposes
        if is_checked_out and (has_checkin_images or checkout_is_future):
            print(f"[DEBUG]   WARNING: Status is 'checked_out' but has check-in images or future checkout date.")
            print(f"[DEBUG]   Has check-in images: {has_checkin_images}, Checkout is future: {checkout_is_future}")
            print(f"[DEBUG]   Allowing extension due to data inconsistency - treating as checked-in.")
            # Treat as checked-in for extension purposes
            is_checked_out = False
            is_valid_for_extension = True
        
        # Reject checked-out statuses first (unless they have check-in images)
        if is_checked_out:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot extend checkout for package booking with status '{booking.status}'. The guest has already checked out. If this booking was checked in, please refresh the page or contact support."
            )
        
        # Then check if it's a valid status for extension
        if not is_valid_for_extension:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot extend checkout for package booking with status '{booking.status}'. Only 'booked' or 'checked-in' bookings can be extended."
            )
    
    # Validate that new checkout date is after current checkout date
    if new_checkout_date <= booking.check_out:
        raise HTTPException(
            status_code=400, 
            detail=f"New checkout date ({new_checkout_date}) must be after current checkout date ({booking.check_out})"
        )
    
    # Check for conflicts with other bookings on the same rooms
    room_ids = [br.room_id for br in booking.rooms if br.room_id]
    
    if room_ids:
        # Check for conflicts with regular bookings
        from app.models.booking import Booking, BookingRoom
        conflicting_bookings = db.query(Booking).join(BookingRoom).filter(
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
        
        # Check for conflicts with other package bookings
        conflicting_package_bookings = db.query(PackageBooking).join(PackageBookingRoom).filter(
            PackageBooking.id != booking_id,
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
                detail=f"Cannot extend checkout date. Room(s) are already booked by another package booking (ID: {conflicting_package_bookings.id}) during the extended period."
            )
    
    # Update the checkout date
    booking.check_out = new_checkout_date
    db.commit()
    db.refresh(booking)
    
    # Reload booking with relationships for response
    booking_with_rooms = db.query(PackageBooking).options(
        joinedload(PackageBooking.rooms).joinedload(PackageBookingRoom.room),
        joinedload(PackageBooking.package)
    ).filter(PackageBooking.id == booking_id).first()
    
    return booking_with_rooms

@router.put("/booking/{booking_id}/check-in", response_model=PackageBookingOut)
def check_in_package_booking(
    booking_id: Union[str, int],
    id_card_image: UploadFile = File(...),
    guest_photo: UploadFile = File(...),
    amenityAllocation: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        with open("debug_pkg_checkin.txt", "a") as f:
            f.write(f"\n--- NEW REQUEST {datetime.now()} ---\n")
            f.write(f"Booking ID: {booking_id}\n")
            f.write(f"Amenity Allocation Raw: {amenityAllocation}\n")
    except Exception as e:
        print(f"Log error: {e}")

    # Parse display ID (PK-000001) or accept numeric ID
    numeric_id, booking_type = parse_display_id(str(booking_id))
    if numeric_id is None:
        raise HTTPException(status_code=400, detail=f"Invalid booking ID format: {booking_id}")
    if booking_type and booking_type != "package":
        raise HTTPException(status_code=400, detail=f"Invalid booking type. Expected package booking, got: {booking_id}")
    booking_id = numeric_id
    
    booking = (
        db.query(PackageBooking)
        .options(joinedload(PackageBooking.rooms).joinedload(PackageBookingRoom.room))
        .filter(PackageBooking.id == booking_id).first()
    )
    if not booking:
        raise HTTPException(status_code=404, detail="Package booking not found")

    # Normalize status to be robust against case/whitespace/underscore differences
    normalized_status = (booking.status or "").strip().lower().replace("_", "-")
    # Allow check-in when:
    #  - status is 'booked' (normal case), OR
    #  - status is 'checked-out' but no check-in images were ever saved (recover-from-state issue)
    # This prevents lock-out when UI shows BOOKED but DB flipped due to earlier process.
    recoverable_checked_out = (
        normalized_status == "checked-out" and not booking.id_card_image_url and not booking.guest_photo_url
    )
    if normalized_status != "booked" and not recoverable_checked_out:
        raise HTTPException(
            status_code=400,
            detail=f"Package booking {booking_id} cannot be checked in. Expected status 'booked', found '{booking.status}'."
        )

    # PROCESS AMENITY ALLOCATION AND SCHEDULED FOOD ORDERS
    if amenityAllocation:
        print(f"[DEBUG] Received amenityAllocation: {amenityAllocation}")

        print(f"DEBUG: Received amenityAllocation: {amenityAllocation}")
        try:
            import json
            from app.models.foodorder import FoodOrder, FoodOrderItem
            from app.models.food_item import FoodItem
            from datetime import datetime, timedelta, date
            
            alloc_data = json.loads(amenityAllocation)
            if not alloc_data:
                print("DEBUG: alloc_data is empty or None")
            else:
                items = alloc_data.get("items", [])
                
                # Find the first room ID for assignment
                room_id = None
                if booking.rooms and len(booking.rooms) > 0:
                    room_id = booking.rooms[0].room_id
                
                print(f"[DEBUG] Processing {len(items)} items for room_id {room_id}")
                
                print(f"DEBUG: Processing {len(items)} items for room_id {room_id}")
                
                if items and room_id:
                    check_in_date = date.today()
                    
                    for item in items:
                        name = item.get("name")
                        scheduled_time = item.get("scheduledTime")
                        scheduled_date_str = item.get("scheduledDate")
                        
                        print(f"[DEBUG] Item {name}, Time: {scheduled_time}, Date: {scheduled_date_str}")
                        
                        print(f"DEBUG: Item {name}, Time: {scheduled_time}, Date: {scheduled_date_str}")
                        
                        # Only create Food Order if it has a specific schedule
                        if name and scheduled_time:
                            try:
                                 # Construct datetime for the schedule
                                 # scheduled_time is usually "HH:MM"
                                 # Sanitize time string just in case
                                 scheduled_time = scheduled_time.strip()
                                 if " " in scheduled_time:
                                     # Handle "07:20 PM" format if it comes up (though type='time' shouldn't send it)
                                     try:
                                         t = datetime.strptime(scheduled_time, "%I:%M %p")
                                         sh, sm = t.hour, t.minute
                                     except ValueError:
                                         # Try standard fallback
                                         sh, sm = map(int, scheduled_time.split(":")[:2])
                                 else:
                                     sh, sm = map(int, scheduled_time.split(":")[:2])
                                 
                                 if scheduled_date_str:
                                     # Use provided date
                                     s_year, s_month, s_day = map(int, scheduled_date_str.split("-"))
                                     scheduled_dt = datetime(s_year, s_month, s_day, sh, sm)
                                 else:
                                     # Fallback to smart logic: today or tomorrow
                                     now = datetime.now()
                                     scheduled_dt = datetime.combine(check_in_date, datetime.min.time().replace(hour=sh, minute=sm))
                                     if scheduled_dt < now:
                                         scheduled_dt = scheduled_dt + timedelta(days=1)
                                 
                                 schedule_str = scheduled_dt.strftime("%Y-%m-%d %H:%M:%S")
                                 
                                 # Try to find a matching Food Item to link properly, otherwise just use note
                                 food_item = db.query(FoodItem).filter(FoodItem.name.ilike(name)).first()
                                 
                                 new_order = FoodOrder(
                                     room_id=room_id,
                                     amount=0.0, # Complimentary package item
                                     status="scheduled",
                                     billing_status="unbilled",
                                     order_type="room_service",
                                     delivery_request=f"SCHEDULED_FOR: {schedule_str} -- Package Meal: {name}",
                                     created_at=datetime.utcnow()
                                 )
                                 db.add(new_order)
                                 db.flush() # Get ID
                                 
                                 print(f"[DEBUG] Created scheduled order {new_order.id}")

                                 print(f"DEBUG: Created scheduled order {new_order.id}")
                                 
                                 # Logic for adding items to the order
                                 specific_items = item.get("specificFoodItems", [])
                                 items_added = False

                                 if specific_items and len(specific_items) > 0:
                                     print(f"DEBUG: Processing {len(specific_items)} specific food items for order {new_order.id}")
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
                                     # Try to find a matching Food Item to link properly
                                     food_item = db.query(FoodItem).filter(FoodItem.name.ilike(name)).first()
                                     if food_item:
                                         order_item = FoodOrderItem(
                                             order_id=new_order.id,
                                             food_item_id=food_item.id,
                                             quantity=item.get("complimentaryPerNight", 1) # Use daily qty
                                         )
                                         db.add(order_item)
                                 
                            except Exception as e:
                                print(f"[ERROR] Error creating scheduled order for {name}: {e}")
                                import traceback
                                traceback.print_exc()
                            
        except Exception as e:
            print(f"[ERROR] Error processing amenity allocation in check-in: {e}")
            print(f"Error processing amenity allocation in check-in: {e}")
            import traceback
            traceback.print_exc()

    # Save ID card image
    id_card_filename = f"id_pkg_{booking_id}_{uuid.uuid4().hex}.jpg"
    id_card_path = os.path.join(CHECKIN_UPLOAD_DIR, id_card_filename)
    with open(id_card_path, "wb") as buffer:
        shutil.copyfileobj(id_card_image.file, buffer)
    booking.id_card_image_url = id_card_filename

    # Save guest photo
    guest_photo_filename = f"guest_pkg_{booking_id}_{uuid.uuid4().hex}.jpg"
    guest_photo_path = os.path.join(CHECKIN_UPLOAD_DIR, guest_photo_filename)
    with open(guest_photo_path, "wb") as buffer:
        shutil.copyfileobj(guest_photo.file, buffer)
    booking.guest_photo_url = guest_photo_filename

    booking.status = "checked-in"
    # Set the actual check-in timestamp for strict bill scoping
    from datetime import datetime
    booking.checked_in_at = datetime.utcnow()
    booking.user_id = current_user.id

    if booking.rooms:
        room_ids = [br.room_id for br in booking.rooms]
        db.query(Room).filter(Room.id.in_(room_ids)).update({"status": "Checked-in"}, synchronize_session=False)

    db.commit()
    db.refresh(booking)
    return booking

# -------------------------------
# GET check-in images for packages
# -------------------------------
@router.get("/booking/checkin-image/{filename}")
def get_package_checkin_image(filename: str):
    filepath = os.path.join(CHECKIN_UPLOAD_DIR, filename)
    if not os.path.exists(filepath) or not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(filepath)
