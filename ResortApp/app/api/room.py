from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Query
import os
# Absolute project root path (ResortApp/)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_UPLOAD_ROOT = os.path.join(_BASE_DIR, "uploads")
from typing import Optional, List, Union
import json
from app.utils.auth import get_current_user, require_permission
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import SessionLocal
from app.schemas.room import RoomCreate, RoomOut
from app.curd import room as crud_room
from app.models.room import Room, RoomType
from app.models.booking import Booking, BookingRoom
import shutil
from app.utils.branch_scope import get_branch_id
from app.models.user import User
from uuid import uuid4
from app.schemas.room_type import RoomTypeCreate, RoomTypeUpdate, RoomType as RoomTypeOut, RoomTypeAvailability
from app.models.inventory import InventoryTransaction, InventoryItem, Location
from app.models.employee import Employee
from app.models.service_request import ServiceRequest

from datetime import date
from app.utils.date_utils import get_ist_now, get_ist_today, format_iso_z

router = APIRouter(prefix="/rooms", tags=["Rooms"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

UPLOAD_DIR = os.path.join(_UPLOAD_ROOT, "rooms")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- RoomType Endpoints ---

@router.get("/types", response_model=List[RoomTypeOut])
def get_room_types(db: Session = Depends(get_db), branch_id: int = Depends(get_branch_id)):
    query = db.query(RoomType)
    if branch_id:
        query = query.filter(RoomType.branch_id == branch_id)
    return query.all()

@router.get("/types/all", response_model=List[RoomTypeOut])
def get_room_types_all(db: Session = Depends(get_db), branch_id: int = Depends(get_branch_id)):
    """Alias for /types to support legacy mobile requests"""
    return get_room_types(db, branch_id)

@router.post("/types", response_model=RoomTypeOut)
def create_room_type(
    name: str = Form(...),
    base_price: float = Form(0.0),
    weekend_price: Optional[float] = Form(None),
    long_weekend_price: Optional[float] = Form(None),
    holiday_price: Optional[float] = Form(None),
    total_inventory: int = Form(0),
    capacity: int = Form(2),
    children_capacity: int = Form(0),
    extra_bed_price: float = Form(0.0),
    channel_manager_id: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
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
    tv: bool = Form(False),
    balcony: bool = Form(False),
    mountain_view: bool = Form(False),
    ocean_view: bool = Form(False),
    private_pool: bool = Form(False),
    hot_tub: bool = Form(False),
    fireplace: bool = Form(False),
    pet_friendly: bool = Form(False),
    wheelchair_accessible: bool = Form(False),
    safe_box: bool = Form(False),
    room_service: bool = Form(False),
    laundry_service: bool = Form(False),
    gym_access: bool = Form(False),
    spa_access: bool = Form(False),
    housekeeping: bool = Form(False),
    mini_bar: bool = Form(False),
    rate_plans_json: Optional[str] = Form(None),
    branch_id: int = Form(1),
    images: List[UploadFile] = File(None),
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_permission("rooms:create")),
    scoped_branch_id: Optional[int] = Depends(get_branch_id),
    *,
    background_tasks: BackgroundTasks
):
    effective_branch_id = scoped_branch_id if scoped_branch_id is not None else branch_id
    
    image_urls = []
    if images:
        for img in images:
            if img.filename:
                try:
                    ext = img.filename.split('.')[-1]
                    filename = f"roomtype_{uuid4().hex}.{ext}"
                    image_path = os.path.join(UPLOAD_DIR, filename)
                    with open(image_path, "wb") as buffer:
                        shutil.copyfileobj(img.file, buffer)
                    image_urls.append(f"/uploads/rooms/{filename}")
                except Exception as e:
                    print(f"Error saving image: {e}")
                    
    main_image = image_urls[0] if image_urls else None
    extra_imgs = json.dumps(image_urls[1:]) if len(image_urls) > 1 else None

    db_room_type = RoomType(
        name=name,
        base_price=base_price,
        weekend_price=weekend_price,
        long_weekend_price=long_weekend_price,
        holiday_price=holiday_price,
        total_inventory=total_inventory,
        adults_capacity=capacity,
        children_capacity=children_capacity,
        channel_manager_id=channel_manager_id,
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
        tv=tv,
        balcony=balcony,
        mountain_view=mountain_view,
        ocean_view=ocean_view,
        private_pool=private_pool,
        hot_tub=hot_tub,
        fireplace=fireplace,
        pet_friendly=pet_friendly,
        wheelchair_accessible=wheelchair_accessible,
        safe_box=safe_box,
        room_service=room_service,
        laundry_service=laundry_service,
        gym_access=gym_access,
        spa_access=spa_access,
        housekeeping=housekeeping,
        mini_bar=mini_bar,
        branch_id=effective_branch_id,
        image_url=main_image,
        extra_images=extra_imgs
    )
    db.add(db_room_type)
    db.commit()
    db.refresh(db_room_type)

    if rate_plans_json:
        try:
            plans = json.loads(rate_plans_json)
            from app.models.room import RatePlan
            for plan in plans:
                db_plan = RatePlan(
                    name=plan.get("name", "Unnamed Plan"),
                    room_type_id=db_room_type.id,
                    occupancy=int(plan.get("occupancy", 2)),
                    meal_plan=plan.get("meal_plan", "CP"),
                    channel_manager_id=plan.get("channel_manager_id"),
                    base_price=float(plan.get("base_price", 0.0)),
                    price_offset=float(plan.get("price_offset", 0.0)),
                    branch_id=effective_branch_id
                )
                db.add(db_plan)
            db.commit()
        except Exception as e:
            print(f"Error saving rate plans: {e}")

    if background_tasks:
        try:
            from app.core.aiosell_triggers import trigger_inventory_push, trigger_rates_push
            background_tasks.add_task(trigger_inventory_push, db_room_type.id)
            background_tasks.add_task(trigger_rates_push, db_room_type.id)
        except Exception as e:
            print(f"Failed to queue Aiosell sync: {e}")

    return db_room_type

@router.put("/types/{type_id}", response_model=RoomTypeOut)
def update_room_type(
    type_id: int, 
    name: Optional[str] = Form(None),
    base_price: Optional[float] = Form(None),
    weekend_price: Optional[float] = Form(None),
    long_weekend_price: Optional[float] = Form(None),
    holiday_price: Optional[float] = Form(None),
    total_inventory: Optional[int] = Form(None),
    capacity: Optional[int] = Form(None),
    children_capacity: Optional[int] = Form(None),
    extra_bed_price: Optional[float] = Form(None),
    channel_manager_id: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    air_conditioning: Optional[bool] = Form(None),
    wifi: Optional[bool] = Form(None),
    bathroom: Optional[bool] = Form(None),
    living_area: Optional[bool] = Form(None),
    terrace: Optional[bool] = Form(None),
    parking: Optional[bool] = Form(None),
    kitchen: Optional[bool] = Form(None),
    family_room: Optional[bool] = Form(None),
    bbq: Optional[bool] = Form(None),
    garden: Optional[bool] = Form(None),
    dining: Optional[bool] = Form(None),
    breakfast: Optional[bool] = Form(None),
    tv: Optional[bool] = Form(None),
    balcony: Optional[bool] = Form(None),
    mountain_view: Optional[bool] = Form(None),
    ocean_view: Optional[bool] = Form(None),
    private_pool: Optional[bool] = Form(None),
    hot_tub: Optional[bool] = Form(None),
    fireplace: Optional[bool] = Form(None),
    pet_friendly: Optional[bool] = Form(None),
    wheelchair_accessible: Optional[bool] = Form(None),
    safe_box: Optional[bool] = Form(None),
    room_service: Optional[bool] = Form(None),
    laundry_service: Optional[bool] = Form(None),
    gym_access: Optional[bool] = Form(None),
    spa_access: Optional[bool] = Form(None),
    housekeeping: Optional[bool] = Form(None),
    mini_bar: Optional[bool] = Form(None),
    rate_plans_json: Optional[str] = Form(None),
    existing_images: Optional[str] = Form(None),
    images: List[UploadFile] = File(None),
    *,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_permission("rooms:edit"))
):
    db_room_type = db.query(RoomType).filter(RoomType.id == type_id).first()
    if not db_room_type:
        raise HTTPException(status_code=404, detail="Room Type not found")
    
    if name is not None: db_room_type.name = name
    if base_price is not None: db_room_type.base_price = base_price
    if weekend_price is not None: db_room_type.weekend_price = weekend_price
    if long_weekend_price is not None: db_room_type.long_weekend_price = long_weekend_price
    if holiday_price is not None: db_room_type.holiday_price = holiday_price
    if total_inventory is not None: db_room_type.total_inventory = total_inventory
    if capacity is not None: db_room_type.adults_capacity = capacity
    if children_capacity is not None: db_room_type.children_capacity = children_capacity
    if channel_manager_id is not None and channel_manager_id != "": db_room_type.channel_manager_id = channel_manager_id
    if air_conditioning is not None: db_room_type.air_conditioning = air_conditioning
    if wifi is not None: db_room_type.wifi = wifi
    if bathroom is not None: db_room_type.bathroom = bathroom
    if living_area is not None: db_room_type.living_area = living_area
    if terrace is not None: db_room_type.terrace = terrace
    if parking is not None: db_room_type.parking = parking
    if kitchen is not None: db_room_type.kitchen = kitchen
    if family_room is not None: db_room_type.family_room = family_room
    if bbq is not None: db_room_type.bbq = bbq
    if garden is not None: db_room_type.garden = garden
    if dining is not None: db_room_type.dining = dining
    if breakfast is not None: db_room_type.breakfast = breakfast
    if tv is not None: db_room_type.tv = tv
    if balcony is not None: db_room_type.balcony = balcony
    if mountain_view is not None: db_room_type.mountain_view = mountain_view
    if ocean_view is not None: db_room_type.ocean_view = ocean_view
    if private_pool is not None: db_room_type.private_pool = private_pool
    if hot_tub is not None: db_room_type.hot_tub = hot_tub
    if fireplace is not None: db_room_type.fireplace = fireplace
    if pet_friendly is not None: db_room_type.pet_friendly = pet_friendly
    if wheelchair_accessible is not None: db_room_type.wheelchair_accessible = wheelchair_accessible
    if safe_box is not None: db_room_type.safe_box = safe_box
    if room_service is not None: db_room_type.room_service = room_service
    if laundry_service is not None: db_room_type.laundry_service = laundry_service
    if gym_access is not None: db_room_type.gym_access = gym_access
    if spa_access is not None: db_room_type.spa_access = spa_access
    if housekeeping is not None: db_room_type.housekeeping = housekeeping
    if mini_bar is not None: db_room_type.mini_bar = mini_bar

    current_image_url = db_room_type.image_url
    try:
        current_extras = json.loads(db_room_type.extra_images) if db_room_type.extra_images else []
    except:
        current_extras = []
    
    all_current_urls = ([current_image_url] if current_image_url else []) + current_extras
    
    if existing_images is not None:
        try:
            keep_urls = json.loads(existing_images)
            for url in all_current_urls:
                if url not in keep_urls:
                    path = url.lstrip("/")
                    if os.path.exists(path):
                        try: os.remove(path)
                        except: pass
            if keep_urls:
                current_image_url = keep_urls[0]
                current_extras = keep_urls[1:]
            else:
                current_image_url = None
                current_extras = []
        except:
            pass

    if images:
        new_urls = []
        for img in images:
            if img.filename:
                ext = img.filename.split('.')[-1]
                filename = f"roomtype_{uuid4().hex}.{ext}"
                image_path = os.path.join(UPLOAD_DIR, filename)
                with open(image_path, "wb") as buffer:
                    shutil.copyfileobj(img.file, buffer)
                new_urls.append(f"/uploads/rooms/{filename}")
        
        if new_urls:
            if not current_image_url:
                current_image_url = new_urls.pop(0)
            current_extras.extend(new_urls)

    db_room_type.image_url = current_image_url
    db_room_type.extra_images = json.dumps(current_extras) if current_extras else None

    db.commit()
    db.refresh(db_room_type)

    if rate_plans_json:
        try:
            plans = json.loads(rate_plans_json)
            from app.models.room import RatePlan
            # Delete old ones or update? For simplicity, we'll replace them
            db.query(RatePlan).filter(RatePlan.room_type_id == type_id).delete()
            for plan in plans:
                db_plan = RatePlan(
                    name=plan.get("name", "Unnamed Plan"),
                    room_type_id=db_room_type.id,
                    occupancy=int(plan.get("occupancy", 2)),
                    meal_plan=plan.get("meal_plan", "CP"),
                    channel_manager_id=plan.get("channel_manager_id"),
                    base_price=float(plan.get("base_price", 0.0)),
                    price_offset=float(plan.get("price_offset", 0.0)),
                    branch_id=db_room_type.branch_id
                )
                db.add(db_plan)
            db.commit()
        except Exception as e:
            print(f"Error updating rate plans: {e}")
    
    if background_tasks:
        try:
            from app.core.aiosell_triggers import trigger_rates_push, trigger_inventory_push
            background_tasks.add_task(trigger_rates_push, db_room_type.id)
            background_tasks.add_task(trigger_inventory_push, db_room_type.id)
        except Exception as e:
            print(f"Failed to queue Aiosell sync: {e}")
            
    return db_room_type

@router.delete("/types/{type_id}")
def delete_room_type(
    type_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(require_permission("rooms:delete"))
):
    db_room_type = db.query(RoomType).filter(RoomType.id == type_id).first()
    if not db_room_type:
        raise HTTPException(status_code=404, detail="Room Type not found")
    
    # Check if any rooms are using this type
    if db.query(Room).filter(Room.room_type_id == type_id).first():
        raise HTTPException(status_code=400, detail="Cannot delete Room Type while rooms are associated with it")
        
    db.delete(db_room_type)
    db.commit()
    return {"message": "Room Type deleted successfully"}

@router.get("/types/availability", response_model=List[RoomTypeAvailability])
def get_room_type_availability(
    check_in: date, 
    check_out: date, 
    db: Session = Depends(get_db), 
    branch_id: int = Depends(get_branch_id)
):
    room_types = db.query(RoomType).filter(RoomType.branch_id == branch_id).all()
    results = []
    
    for rt in room_types:
        # Overlapping bookings count
        overlapping_count = db.query(Booking).filter(
            Booking.room_type_id == rt.id,
            Booking.status.in_(['booked', 'checked_in', 'occupied']),
            Booking.check_in < check_out,
            Booking.check_out > check_in
        ).count()
        
        results.append(RoomTypeAvailability(
            room_type_id=rt.id,
            name=rt.name,
            available_count=max(0, rt.total_inventory - overlapping_count),
            total_inventory=rt.total_inventory,
            base_price=rt.base_price
        ))
    return results


# Test endpoint without authentication - handles images
@router.post("/test", response_model=RoomOut)
def create_room_test(
    number: str = Form(...),
    room_type_id: int = Form(...),
    status: str = Form("Available"),
    images: List[UploadFile] = File(None),
    branch_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    scoped_branch_id: Optional[int] = Depends(get_branch_id)
):

    # Use explicitly passed branch_id if user is superadmin or it matches scoped branch
    effective_branch_id = scoped_branch_id
    if branch_id is not None:
        if getattr(current_user, "is_superadmin", False) or branch_id == scoped_branch_id:
            effective_branch_id = branch_id
    
    if effective_branch_id is None:
        # Fallback to user's branch if still None
        effective_branch_id = getattr(current_user, "branch_id", None) or 1

    try:
        # Check if room number already exists in this branch
        existing_room = db.query(Room).filter(Room.number == number, Room.branch_id == effective_branch_id).first()

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
        
        db_room = Room(
            number=number,
            room_type_id=room_type_id,
            status=status,
            image_url=main_image,
            extra_images=extra_images,
            branch_id=effective_branch_id
        )

        db.add(db_room)
        db.commit()
        db.refresh(db_room)
        
        # Automatically create location for this room
        try:
            from app.models.inventory import Location
            from app.curd import inventory as inventory_crud
            from sqlalchemy import or_
            
            # Fetch type name
            room_type = db.query(RoomType).filter(RoomType.id == room_type_id).first()
            type_name = room_type.name if room_type else "Standard"

            # Check if location already exists in THIS branch
            existing_location = db.query(Location).filter(
                or_(
                    Location.name == f"Room {number}",
                    Location.room_area == f"Room {number}"
                ),
                Location.location_type == "GUEST_ROOM",
                Location.branch_id == effective_branch_id
            ).first()
            
            if not existing_location:
                location_data = {
                    "name": f"Room {number}",
                    "building": "Main Building",
                    "floor": None,
                    "room_area": f"Room {number}",
                    "location_type": "GUEST_ROOM",
                    "is_inventory_point": False,
                    "description": f"Guest room {number} - {type_name}",
                    "is_active": (status != "Deleted" if status else True)
                }
                location = inventory_crud.create_location(db, location_data, branch_id=effective_branch_id)

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
def delete_room_test(room_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user), branch_id: int = Depends(get_branch_id)):

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
def get_rooms_test(db: Session = Depends(get_db), skip: int = 0, limit: int = 100, current_user: User = Depends(get_current_user), branch_id: int = Depends(get_branch_id)):

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
    room_type_id: int = Form(...),
    status: str = Form("Available"),
    images: List[UploadFile] = File(None),
    *,
    background_tasks: BackgroundTasks,
    branch_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("rooms:create")),
    scoped_branch_id: Optional[int] = Depends(get_branch_id)
):

    # Use explicitly passed branch_id if user is superadmin or it matches scoped branch
    effective_branch_id = scoped_branch_id
    if branch_id is not None:
        if getattr(current_user, "is_superadmin", False) or branch_id == scoped_branch_id:
            effective_branch_id = branch_id
    
    if effective_branch_id is None:
        # Fallback to user's branch if still None
        effective_branch_id = getattr(current_user, "branch_id", None) or 1

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

        db_room = Room(
            number=number,
            room_type_id=room_type_id,
            status=status,
            image_url=main_image,
            extra_images=extra_images,
            branch_id=effective_branch_id
        )

        db.add(db_room)
        db.commit()
        db.refresh(db_room)
        
        # Automatically create location for this room
        try:
            from app.models.inventory import Location
            from app.curd import inventory as inventory_crud
            from sqlalchemy import or_
            
            # Fetch room type name for location description
            room_type = db.query(RoomType).filter(RoomType.id == room_type_id).first()
            type_name = room_type.name if room_type else "Standard"

            # Check if location already exists in THIS branch
            existing_location = db.query(Location).filter(
                or_(
                    Location.name == f"Room {number}",
                    Location.room_area == f"Room {number}"
                ),
                Location.location_type == "GUEST_ROOM",
                Location.branch_id == effective_branch_id
            ).first()
            
            if not existing_location:
                location_data = {
                    "name": f"Room {number}",
                    "building": "Main Building",
                    "floor": None,
                    "room_area": f"Room {number}",
                    "location_type": "GUEST_ROOM",
                    "is_inventory_point": False,
                    "description": f"Guest room {number} - {type_name}",
                    "is_active": (status != "Deleted" if status else True)
                }
                location = inventory_crud.create_location(db, location_data, branch_id=effective_branch_id)
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
            
        if background_tasks:
            try:
                from app.core.aiosell_triggers import trigger_inventory_push
                trigger_inventory_push(db, background_tasks, db_room.room_type_id)
            except Exception as e:
                print(f"Failed to queue Aiosell inventory push: {e}")
        
        return db_room
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        print(f"Error creating room: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating room: {str(e)}")


# ---------------- READ ----------------
@router.post("/update-statuses")
def update_room_statuses_endpoint(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), branch_id: int = Depends(get_branch_id)):

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

def _get_rooms_impl(db: Session, branch_id: int, skip: int = 0, limit: int = 20, status: Optional[str] = None, room_type_id: Optional[Union[int, str]] = None):

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
                update_room_statuses(db, branch_id=branch_id)
            except Exception as status_error:
                print(f"Room status update failed (continuing): {status_error}")
                # Continue fetching rooms even if status update fails
        else:
            print(f"Skipping room status update for large query (limit={limit}) to prevent timeout")
        
        # Query rooms with proper error handling - ORDER BY number to ensure consistent ordering
        try:
            from sqlalchemy.orm import joinedload
            q = db.query(Room).options(joinedload(Room.room_type))
            if branch_id is not None:
                q = q.filter(Room.branch_id == branch_id)
            
            if status:
                q = q.filter(Room.status == status)
            
            if room_type_id is not None:
                if isinstance(room_type_id, str):
                    if "," in room_type_id:
                        # Handle comma-separated list
                        try:
                            ids = [int(x.strip()) for x in room_type_id.split(",") if x.strip()]
                            if ids:
                                q = q.filter(Room.room_type_id.in_(ids))
                        except ValueError:
                            # Fallback if malformed
                            pass
                    else:
                        # Single ID string
                        try:
                            q = q.filter(Room.room_type_id == int(room_type_id))
                        except ValueError:
                            # Ignore if not an integer string
                            pass
                else:
                    # Single ID (int)
                    q = q.filter(Room.room_type_id == room_type_id)

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
def get_rooms(
    db: Session = Depends(get_db), 
    skip: int = 0, 
    limit: int = 20, 
    status: Optional[str] = None, 
    room_type_id: Optional[Union[int, str]] = None, 
    branch_id_query: Optional[int] = Query(None, alias="branch_id"),
    current_user: User = Depends(require_permission("rooms:view")), 
    branch_id: int = Depends(get_branch_id)
):
    effective_branch_id = branch_id_query if branch_id_query is not None else branch_id
    print(f"[DEBUG-ROOMS] Fetching rooms for effective_branch_id: {effective_branch_id} (Query: {branch_id_query}, Context: {branch_id})")
    return _get_rooms_impl(db, effective_branch_id, skip, limit, status, room_type_id)


@router.get("/", response_model=list[RoomOut])  # Handle trailing slash
def get_rooms_slash(
    db: Session = Depends(get_db), 
    skip: int = 0, 
    limit: int = 20, 
    status: Optional[str] = None, 
    room_type_id: Optional[Union[int, str]] = None, 
    branch_id_query: Optional[int] = Query(None, alias="branch_id"),
    current_user: User = Depends(get_current_user), 
    branch_id: int = Depends(get_branch_id)
):
    effective_branch_id = branch_id_query if branch_id_query is not None else branch_id
    return _get_rooms_impl(db, effective_branch_id, skip, limit, status, room_type_id)



# ---------------- DELETE ----------------
@router.delete("/{room_id}")
def delete_room(room_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(require_permission("rooms:delete")), branch_id: int = Depends(get_branch_id)):

    db_room = db.query(Room).filter(Room.id == room_id, Room.branch_id == branch_id).first()

    if db_room is None:
        raise HTTPException(status_code=404, detail="Room not found")

    # Delete associated image if exists
    if db_room.image_url:
        image_path = db_room.image_url.lstrip("/")
        if os.path.exists(image_path):
            os.remove(image_path)

    # Capture location ID and type before deleting room
    inv_loc_id = db_room.inventory_location_id
    room_type_id = db_room.room_type_id

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
    
    if background_tasks and room_type_id:
        try:
            from app.core.aiosell_triggers import trigger_inventory_push
            trigger_inventory_push(db, background_tasks, room_type_id)
        except Exception as e:
            print(f"Failed to queue Aiosell inventory push: {e}")
            
    return {"message": "Room deleted successfully"}


# ---------------- UPDATE ----------------
@router.put("/{room_id}", response_model=RoomOut)
def update_room(
    room_id: int,
    number: str = Form(None),
    room_type_id: int = Form(None),
    status: str = Form(None),
    housekeeping_status: str = Form(None),
    images: List[UploadFile] = File(None),
    existing_images: str = Form(None), # JSON list of image URLs to keep
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(require_permission("rooms:edit")),
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
    if room_type_id is not None:
        db_room.room_type_id = room_type_id
    if status:
        if db_room.status == "Maintenance" and status == "Available":
             db_room.last_maintenance_date = get_ist_today().date()
        db_room.status = status
    if housekeeping_status:
        db_room.housekeeping_status = housekeeping_status

    # --- IMAGE HANDLING ---
    current_image_url = db_room.image_url
    try:
        current_extras = json.loads(db_room.extra_images) if db_room.extra_images else []
    except:
        current_extras = []
    
    all_current_urls = ([current_image_url] if current_image_url else []) + current_extras
    
    # 1. Handle selective deletion if existing_images is provided
    if existing_images is not None:
        try:
            keep_urls = json.loads(existing_images)
            # Identify urls to delete from disk
            for url in all_current_urls:
                if url not in keep_urls:
                    path = url.lstrip("/")
                    if os.path.exists(path):
                        try: os.remove(path)
                        except: pass
            
            # Reconstruct current state from keep_urls
            if keep_urls:
                current_image_url = keep_urls[0]
                current_extras = keep_urls[1:]
            else:
                current_image_url = None
                current_extras = []
        except Exception as e:
            print(f"Error parsing existing_images: {e}")

    # 2. Handle new uploads
    if images:
        new_urls = []
        for img in images:
            if img.filename:
                ext = img.filename.split(".")[-1]
                filename = f"room_{uuid4().hex}.{ext}"
                image_path = os.path.join(UPLOAD_DIR, filename)
                with open(image_path, "wb") as buffer:
                    shutil.copyfileobj(img.file, buffer)
                new_urls.append(f"/uploads/rooms/{filename}")
        
        if new_urls:
            if not current_image_url:
                current_image_url = new_urls.pop(0)
            current_extras.extend(new_urls)

    # 3. Final Sync to DB
    db_room.image_url = current_image_url
    db_room.extra_images = json.dumps(current_extras) if current_extras else None

    db.commit()
    db.refresh(db_room)
    
    if background_tasks:
        try:
            from app.core.aiosell_triggers import trigger_inventory_push
            trigger_inventory_push(db, background_tasks, db_room.room_type_id)
        except Exception as e:
            print(f"Failed to queue Aiosell inventory push: {e}")
            
    return db_room

@router.get("/stats")
def get_room_stats(db: Session = Depends(get_db), branch_id: int = Depends(get_branch_id)):
    def bscope(q):
        return q.filter(Room.branch_id == branch_id) if branch_id is not None else q
    total = bscope(db.query(Room)).count()
    occupied = bscope(db.query(Room).filter(Room.status.in_(["Occupied", "Checked-in", "Booked"]))).count()
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


# ---------------- ROOM ACTIVITY TRACKING ----------------
@router.get("/{room_id}/inventory-usage")
def get_room_inventory_usage(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get inventory usage history for a specific room.
    Returns items consumed/used in this room with employee and guest information.
    """
    try:
        # Get room to verify it exists
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        
        # Get inventory transactions for this room's location
        if not room.inventory_location_id:
            return []
        
        from sqlalchemy import or_
        transactions = db.query(InventoryTransaction).filter(
            or_(
                InventoryTransaction.source_location_id == room.inventory_location_id,
                InventoryTransaction.destination_location_id == room.inventory_location_id
            )
        ).order_by(InventoryTransaction.created_at.desc()).limit(100).all()
        
        result = []
        for trans in transactions:
            item = db.query(InventoryItem).filter(InventoryItem.id == trans.item_id).first()
            employee = db.query(Employee).filter(Employee.id == trans.employee_id).first() if hasattr(trans, 'employee_id') and trans.employee_id else None
            
            # Use created_at if transaction_date doesn't exist
            timestamp = trans.transaction_date if hasattr(trans, 'transaction_date') else trans.created_at

            result.append({
                "item_name": item.name if item else "Unknown Item",
                "quantity": abs(trans.quantity) if trans.transaction_type in ['consumption', 'sale'] else trans.quantity,
                "used_by_name": employee.name if employee else "System",
                "used_at": format_iso_z(timestamp),
                "guest_used": trans.transaction_type == 'sale',  # Sales are typically guest-related
                "transaction_type": trans.transaction_type,
                "notes": trans.notes
            })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching room inventory usage: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching inventory usage: {str(e)}")

@router.get("/{room_id}/activity-log")
def get_room_activity_log(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get complete activity log for a specific room including:
    - Service requests
    - Cleaning/housekeeping
    - Bookings (check-ins/check-outs)
    - Maintenance activities
    """
    try:
        # Get room to verify it exists
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        
        activities = []
        
        # 1. Service Requests
        service_requests = db.query(ServiceRequest).filter(
            ServiceRequest.room_id == room_id
        ).order_by(ServiceRequest.created_at.desc()).limit(50).all()
        
        for sr in service_requests:
            employee = db.query(Employee).filter(Employee.id == sr.employee_id).first() if sr.employee_id else None
            activities.append({
                "type": "service",
                "description": f"{sr.request_type}: {sr.description or 'No description'}",
                "performed_by": employee.name if employee else "Unassigned",
                "timestamp": format_iso_z(sr.completed_at) if (hasattr(sr, 'completed_at') and sr.completed_at) else format_iso_z(sr.created_at),
                "status": sr.status
            })
        
        # 2. Bookings (Check-ins/Check-outs)
        bookings = db.query(Booking).join(BookingRoom).filter(
            BookingRoom.room_id == room_id
        ).order_by(Booking.check_in.desc()).limit(20).all()
        
        for booking in bookings:
            # Check-in activity
            activities.append({
                "type": "booking",
                "description": f"Guest check-in: {booking.guest_name}",
                "performed_by": "Front Desk",
                "timestamp": format_iso_z(booking.check_in),
                "status": booking.status
            })
            
            # Check-out activity (if applicable)
            if booking.check_out and booking.status in ['checked-out', 'completed']:
                activities.append({
                    "type": "booking",
                    "description": f"Guest check-out: {booking.guest_name}",
                    "performed_by": "Front Desk",
                    "timestamp": format_iso_z(booking.check_out),
                    "status": booking.status
                })
        
        # Sort all activities by timestamp (most recent first)
        activities.sort(key=lambda x: x['timestamp'] if x['timestamp'] else '', reverse=True)
        
        return activities[:100]  # Return top 100 most recent activities
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching room activity log: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching activity log: {str(e)}")
