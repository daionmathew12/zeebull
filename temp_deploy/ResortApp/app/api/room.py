from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import Optional, List
import json
from app.utils.auth import get_current_user
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import SessionLocal
from app.schemas.room import RoomCreate, RoomOut
from app.curd import room as crud_room
from app.models.room import Room
from app.models.booking import Booking, BookingRoom
import shutil
import os
from app.utils.branch_scope import get_branch_id
from uuid import uuid4

from datetime import date

router = APIRouter(prefix="/rooms", tags=["Rooms"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

UPLOAD_DIR = os.path.join("uploads", "rooms")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# Test endpoint without authentication - handles images
@router.post("/test", response_model=RoomOut)
def create_room_test(
    number: str = Form(...),
    type: str = Form(...),
    price: float = Form(...),
    status: str = Form("Available"),
    adults: int = Form(2),
    children: int = Form(0),
    air_conditioning: bool = Form(False),
    wifi: bool = Form(False),
    bathroom: bool = Form(False),
    living_area: bool = Form(False),
    terrace: bool = Form(False),
    parking: bool = Form(False),
    kitchen: bool = Form(False),
    family_room: bool = Form(False),
    bbq: bool = Form(False),
    garden: bool = Form(False),
    dining: bool = Form(False),
    breakfast: bool = Form(False),
    images: List[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):

    try:
        # Check if room number already exists in this branch
        existing_room = db.query(Room).filter(Room.number == number, Room.branch_id == branch_id).first()

        if existing_room:
            raise HTTPException(status_code=400, detail=f"Room {number} already exists")

        image_urls = []
        if images:
            for img in images:
                if img.filename:
                    try:
                        ext = img.filename.split('.')[-1]
                        filename = f"room_{uuid4().hex}.{ext}"
                        image_path = os.path.join(UPLOAD_DIR, filename)
                        with open(image_path, "wb") as buffer:
                            shutil.copyfileobj(img.file, buffer)
                        image_urls.append(f"/uploads/rooms/{filename}")
                    except Exception as e:
                        print(f"Error saving image: {e}")
        
        main_image = image_urls[0] if image_urls else None
        extra_images = json.dumps(image_urls[1:]) if len(image_urls) > 1 else None

        # Convert string booleans to actual booleans (frontend sends "true"/"false" as strings)
        def str_to_bool(val):
            if isinstance(val, bool):
                return val
            if isinstance(val, str):
                return val.lower() in ('true', '1', 'yes')
            return bool(val)
        
        air_conditioning = str_to_bool(air_conditioning)
        wifi = str_to_bool(wifi)
        bathroom = str_to_bool(bathroom)
        living_area = str_to_bool(living_area)
        terrace = str_to_bool(terrace)
        parking = str_to_bool(parking)
        kitchen = str_to_bool(kitchen)
        family_room = str_to_bool(family_room)
        bbq = str_to_bool(bbq)
        garden = str_to_bool(garden)
        dining = str_to_bool(dining)
        breakfast = str_to_bool(breakfast)


        db_room = Room(
            number=number,
            type=type,
            price=price,
            status=status,
            adults=adults,
            children=children,
            image_url=main_image,
            extra_images=extra_images,
            air_conditioning=air_conditioning,
            wifi=wifi,
            bathroom=bathroom,
            living_area=living_area,
            terrace=terrace,
            parking=parking,
            kitchen=kitchen,
            family_room=family_room,
            bbq=bbq,
            garden=garden,
            dining=dining,
            breakfast=breakfast,
            branch_id=branch_id
        )

        db.add(db_room)
        db.commit()
        db.refresh(db_room)
        
        # Automatically create location for this room
        try:
            from app.models.inventory import Location
            from app.curd import inventory as inventory_crud
            from sqlalchemy import or_
            
            # Check if location already exists
            existing_location = db.query(Location).filter(
                or_(
                    Location.name == f"Room {number}",
                    Location.room_area == f"Room {number}"
                ),
                Location.location_type == "GUEST_ROOM"
            ).first()
            
            if not existing_location:
                location_data = {
                    "name": f"Room {number}",
                    "building": "Main Building",
                    "floor": None,
                    "room_area": f"Room {number}",
                    "location_type": "GUEST_ROOM",
                    "is_inventory_point": False,
                    "description": f"Guest room {number} - {type or 'Standard'}",
                    "is_active": (status != "Deleted" if status else True),
                    "branch_id": branch_id
                }
                location = inventory_crud.create_location(db, location_data)

                db_room.inventory_location_id = location.id
                db.commit()
                db.refresh(db_room)
            else:
                db_room.inventory_location_id = existing_location.id
                db.commit()
                db.refresh(db_room)
        except Exception as loc_error:
            # Don't fail room creation if location creation fails
            print(f"Warning: Could not create location for room {number}: {str(loc_error)}")
        
        return db_room
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        print(f"Error creating room: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating room: {str(e)}")


# Test endpoint to check if the router is working
@router.get("/test-simple")
def test_simple():
    return {"message": "Room router is working"}

# Test delete endpoint
@router.delete("/test/{room_id}")
def delete_room_test(room_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user), branch_id: int = Depends(get_branch_id)):

    try:
        db_room = db.query(Room).filter(Room.id == room_id, Room.branch_id == branch_id).first()

        if db_room is None:
            raise HTTPException(status_code=404, detail="Room not found")

        # Delete associated image if exists
        if db_room.image_url:
            image_path = db_room.image_url.lstrip("/")
            if os.path.exists(image_path):
                os.remove(image_path)

        db.delete(db_room)
        db.commit()
        return {"message": "Room deleted successfully"}
    except Exception as e:
        db.rollback()
        print(f"Error deleting room: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting room: {str(e)}")

# Test GET endpoint for fetching rooms
@router.get("/test", response_model=list[RoomOut])
def get_rooms_test(db: Session = Depends(get_db), skip: int = 0, limit: int = 100, current_user: dict = Depends(get_current_user), branch_id: int = Depends(get_branch_id)):

    try:
        # Update room statuses before fetching (non-blocking - continues even if update fails)
        try:
            from app.utils.room_status import update_room_statuses
            update_room_statuses(db)
        except Exception as status_error:
            print(f"Room status update failed (continuing): {status_error}")
            # Continue fetching rooms even if status update fails
        
        q = db.query(Room)
        if branch_id is not None:
            q = q.filter(Room.branch_id == branch_id)
        rooms = q.offset(skip).limit(limit).all()

        return rooms
        
    except Exception as e:
        print(f"Error fetching rooms: {e}")
        print(f"Error type: {type(e)}")
        
        # Try to rollback any pending transaction
        try:
            db.rollback()
        except Exception as rollback_error:
            print(f"Rollback error: {rollback_error}")
        
        raise HTTPException(status_code=500, detail=f"Error fetching rooms: {str(e)}")

@router.post("", response_model=RoomOut)
def create_room(
    number: str = Form(...),
    type: str = Form(...),
    price: float = Form(...),
    status: str = Form("Available"),
    adults: int = Form(2),
    children: int = Form(0),
    air_conditioning: bool = Form(False),
    wifi: bool = Form(False),
    bathroom: bool = Form(False),
    living_area: bool = Form(False),
    terrace: bool = Form(False),
    parking: bool = Form(False),
    kitchen: bool = Form(False),
    family_room: bool = Form(False),
    bbq: bool = Form(False),
    garden: bool = Form(False),
    dining: bool = Form(False),
    breakfast: bool = Form(False),
    images: List[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):

    try:
        image_urls = []
        if images:
            for img in images:
                if img.filename:
                    try:
                        ext = img.filename.split('.')[-1]
                        filename = f"room_{uuid4().hex}.{ext}"
                        image_path = os.path.join(UPLOAD_DIR, filename)
                        with open(image_path, "wb") as buffer:
                            shutil.copyfileobj(img.file, buffer)
                        image_urls.append(f"/uploads/rooms/{filename}")
                    except Exception as e:
                        print(f"Error saving image: {e}")
        
        main_image = image_urls[0] if image_urls else None
        extra_images = json.dumps(image_urls[1:]) if len(image_urls) > 1 else None

        # Convert string booleans to actual booleans (frontend sends "true"/"false" as strings)
        def str_to_bool(val):
            if isinstance(val, bool):
                return val
            if isinstance(val, str):
                return val.lower() in ('true', '1', 'yes')
            return bool(val)
        
        air_conditioning = str_to_bool(air_conditioning)
        wifi = str_to_bool(wifi)
        bathroom = str_to_bool(bathroom)
        living_area = str_to_bool(living_area)
        terrace = str_to_bool(terrace)
        parking = str_to_bool(parking)
        kitchen = str_to_bool(kitchen)
        family_room = str_to_bool(family_room)
        bbq = str_to_bool(bbq)
        garden = str_to_bool(garden)
        dining = str_to_bool(dining)
        breakfast = str_to_bool(breakfast)


        db_room = Room(
            number=number,
            type=type,
            price=price,
            status=status,
            adults=adults,
            children=children,
            image_url=main_image,
            extra_images=extra_images,
            air_conditioning=air_conditioning,
            wifi=wifi,
            bathroom=bathroom,
            living_area=living_area,
            terrace=terrace,
            parking=parking,
            kitchen=kitchen,
            family_room=family_room,
            bbq=bbq,
            garden=garden,
            dining=dining,
            breakfast=breakfast,
            branch_id=branch_id
        )

        db.add(db_room)
        db.commit()
        db.refresh(db_room)
        
        # Automatically create location for this room
        try:
            from app.models.inventory import Location
            from app.curd import inventory as inventory_crud
            from sqlalchemy import or_
            
            # Check if location already exists
            existing_location = db.query(Location).filter(
                or_(
                    Location.name == f"Room {number}",
                    Location.room_area == f"Room {number}"
                ),
                Location.location_type == "GUEST_ROOM"
            ).first()
            
            if not existing_location:
                location_data = {
                    "name": f"Room {number}",
                    "building": "Main Building",
                    "floor": None,
                    "room_area": f"Room {number}",
                    "location_type": "GUEST_ROOM",
                    "is_inventory_point": False,
                    "description": f"Guest room {number} - {type or 'Standard'}",
                    "is_active": (status != "Deleted" if status else True)
                }
                location = inventory_crud.create_location(db, location_data)
                db_room.inventory_location_id = location.id
                db.commit()
                db.refresh(db_room)
            else:
                db_room.inventory_location_id = existing_location.id
                db.commit()
                db.refresh(db_room)
        except Exception as loc_error:
            # Don't fail room creation if location creation fails
            print(f"Warning: Could not create location for room {number}: {str(loc_error)}")
        
        return db_room
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        print(f"Error creating room: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating room: {str(e)}")


# ---------------- READ ----------------
@router.post("/update-statuses")
def update_room_statuses_endpoint(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user), branch_id: int = Depends(get_branch_id)):

    """
    Manually trigger room status update based on current bookings.
    This endpoint can be called to refresh room statuses.
    """
    try:
        from app.utils.room_status import update_room_statuses
        update_room_statuses(db)
        return {"message": "Room statuses updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating room statuses: {str(e)}")

def _get_rooms_impl(db: Session, branch_id: int, skip: int = 0, limit: int = 20):

    """Helper function for get_rooms"""
    try:
        # Optimized for low network - reduced to 50
        if limit > 50:
            limit = 50
        if limit < 1:
            limit = 20
        
        # Test database connection first
        try:
            db.execute(text("SELECT 1"))
        except Exception as conn_error:
            print(f"Database connection test failed: {conn_error}")
            raise HTTPException(status_code=503, detail="Database connection unavailable. Please try again.")
        
        # Skip room status update for large queries (limit > 100) to prevent timeouts
        # Status updates are expensive and can cause 30+ second delays with many rooms
        # For Food Orders page and other bulk operations, we don't need real-time status
        if limit <= 100:
            # Update room statuses before fetching (non-blocking - continues even if update fails)
            try:
                from app.utils.room_status import update_room_statuses
                update_room_statuses(db)
            except Exception as status_error:
                print(f"Room status update failed (continuing): {status_error}")
                # Continue fetching rooms even if status update fails
        else:
            print(f"Skipping room status update for large query (limit={limit}) to prevent timeout")
        
        # Query rooms with proper error handling - ORDER BY number to ensure consistent ordering
        try:
            q = db.query(Room)
            if branch_id is not None:
                q = q.filter(Room.branch_id == branch_id)
            rooms = q.order_by(Room.number).offset(skip).limit(limit).all()

        except Exception as query_error:
            print(f"Room query failed: {query_error}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error querying rooms: {str(query_error)}")
        
        # Return the rooms directly - SQLAlchemy should handle serialization
        from app.models.booking import Booking, BookingRoom
        from app.models.Package import PackageBooking, PackageBookingRoom
        
        if rooms:
            room_ids = [r.id for r in rooms]
            
            # Fetch all regular active bookings for these rooms in one query
            active_bookings = db.query(BookingRoom.room_id, Booking.guest_name).join(Booking).filter(
                BookingRoom.room_id.in_(room_ids),
                Booking.status.in_(['checked-in', 'checked_in', 'Checked-in', 'booked', 'Booked', 'occupied', 'Occupied'])
            ).all()
            regular_booking_map = {b.room_id: b.guest_name for b in active_bookings}
            
            # Fetch all package active bookings for these rooms in one query
            active_pkg_bookings = db.query(PackageBookingRoom.room_id, PackageBooking.guest_name).join(PackageBooking).filter(
                PackageBookingRoom.room_id.in_(room_ids),
                PackageBooking.status.in_(['checked-in', 'checked_in', 'Checked-in', 'booked', 'Booked', 'occupied', 'Occupied'])
            ).all()
            pkg_booking_map = {b.room_id: b.guest_name for b in active_pkg_bookings}
            
            for room in rooms:
                if room.id in regular_booking_map:
                    room.current_guest_name = regular_booking_map[room.id]
                elif room.id in pkg_booking_map:
                    room.current_guest_name = pkg_booking_map[room.id]
                else:
                    room.current_guest_name = None
        
        return rooms
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"Error fetching rooms: {e}")
        print(f"Error type: {type(e)}")
        
        # Try to rollback any pending transaction
        try:
            db.rollback()
        except Exception as rollback_error:
            print(f"Rollback error: {rollback_error}")
        
        raise HTTPException(status_code=500, detail=f"Error fetching rooms: {str(e)}")

@router.get("", response_model=list[RoomOut])
def get_rooms(db: Session = Depends(get_db), skip: int = 0, limit: int = 20, current_user: dict = Depends(get_current_user), branch_id: int = Depends(get_branch_id)):
    return _get_rooms_impl(db, branch_id, skip, limit)


@router.get("/", response_model=list[RoomOut])  # Handle trailing slash
def get_rooms_slash(db: Session = Depends(get_db), skip: int = 0, limit: int = 20, current_user: dict = Depends(get_current_user), branch_id: int = Depends(get_branch_id)):
    return _get_rooms_impl(db, branch_id, skip, limit)



# ---------------- DELETE ----------------
@router.delete("/{room_id}")
def delete_room(room_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user), branch_id: int = Depends(get_branch_id)):

    db_room = db.query(Room).filter(Room.id == room_id, Room.branch_id == branch_id).first()

    if db_room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    # Delete associated image if exists
    if db_room.image_url:
        image_path = db_room.image_url.lstrip("/")
        if os.path.exists(image_path):
            os.remove(image_path)

    # Capture location ID before deleting room
    inv_loc_id = db_room.inventory_location_id

    db.delete(db_room)
    db.flush() # Ensure room deletion is processed mostly (FK constrains)

    # Delete associated inventory location if it exists
    if inv_loc_id:
        try:
            from app.models.inventory import Location
            # Verify it's a guest room location to be safe
            loc = db.query(Location).filter(Location.id == inv_loc_id, Location.location_type == "GUEST_ROOM").first()
            if loc:
                db.delete(loc)
        except Exception as e:
            print(f"Warning: Could not delete associated location {inv_loc_id}: {e}")

    db.commit()
    return {"message": "Room deleted successfully"}


# ---------------- UPDATE ----------------
@router.put("/{room_id}", response_model=RoomOut)
def update_room(
    room_id: int,
    number: str = Form(None),
    type: str = Form(None),
    price: float = Form(None),
    status: str = Form(None),
    housekeeping_status: str = Form(None),
    adults: int = Form(None),
    children: int = Form(None),
    air_conditioning: bool = Form(None),
    wifi: bool = Form(None),
    bathroom: bool = Form(None),
    living_area: bool = Form(None),
    terrace: bool = Form(None),
    parking: bool = Form(None),
    kitchen: bool = Form(None),
    family_room: bool = Form(None),
    bbq: bool = Form(None),
    garden: bool = Form(None),
    dining: bool = Form(None),
    breakfast: bool = Form(None),
    images: List[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):

    q = db.query(Room).filter(Room.id == room_id)
    if branch_id is not None:
        q = q.filter(Room.branch_id == branch_id)
    db_room = q.first()

    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Update fields if provided
    if number:
        db_room.number = number
    if type:
        db_room.type = type
    if price is not None:
        db_room.price = price
    if status:
        if db_room.status == "Maintenance" and status == "Available":
             db_room.last_maintenance_date = date.today()
        db_room.status = status
    if housekeeping_status:
        db_room.housekeeping_status = housekeeping_status
    if adults is not None:
        db_room.adults = adults
    if children is not None:
        db_room.children = children
    
    # Update feature fields if provided
    if air_conditioning is not None:
        db_room.air_conditioning = air_conditioning
    if wifi is not None:
        db_room.wifi = wifi
    if bathroom is not None:
        db_room.bathroom = bathroom
    if living_area is not None:
        db_room.living_area = living_area
    if terrace is not None:
        db_room.terrace = terrace
    if parking is not None:
        db_room.parking = parking
    if kitchen is not None:
        db_room.kitchen = kitchen
    if family_room is not None:
        db_room.family_room = family_room
    if bbq is not None:
        db_room.bbq = bbq
    if garden is not None:
        db_room.garden = garden
    if dining is not None:
        db_room.dining = dining
    if breakfast is not None:
        db_room.breakfast = breakfast

    # Handle new image uploads if provided
    if images:
        # Remove old image if exists
        if db_room.image_url:
            old_path = db_room.image_url.lstrip("/")
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except: pass
        
        # Remove old extra images if they exist
        if db_room.extra_images:
            try:
                old_extras = json.loads(db_room.extra_images)
                for old_p in old_extras:
                    old_path = old_p.lstrip("/")
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except: pass
            except:
                pass

        image_urls = []
        for img in images:
            if img.filename:
                ext = img.filename.split(".")[-1]
                filename = f"room_{uuid4().hex}.{ext}"
                image_path = os.path.join(UPLOAD_DIR, filename)
                with open(image_path, "wb") as buffer:
                    shutil.copyfileobj(img.file, buffer)
                image_urls.append(f"/uploads/rooms/{filename}")
        
        if image_urls:
            db_room.image_url = image_urls[0]
            db_room.extra_images = json.dumps(image_urls[1:]) if len(image_urls) > 1 else None

    db.commit()
    db.refresh(db_room)
    return db_room

@router.get("/stats")
def get_room_stats(db: Session = Depends(get_db), branch_id: int = Depends(get_branch_id)):
    def bscope(q):
        return q.filter(Room.branch_id == branch_id) if branch_id is not None else q
    total = bscope(db.query(Room)).count()
    occupied = bscope(db.query(Room).filter(Room.status == "Occupied")).count()
    available = bscope(db.query(Room).filter(Room.status == "Available")).count()
    maintenance = bscope(db.query(Room).filter(Room.status == "Maintenance")).count()
    dirty = bscope(db.query(Room).filter(Room.housekeeping_status == "Dirty")).count()

    
    return {
        "total": total,
        "occupied": occupied,
        "available": available,
        "maintenance": maintenance,
        "dirty": dirty
    }
