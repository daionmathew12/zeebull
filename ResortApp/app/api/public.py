"""
Public API endpoints for user-facing frontend
These endpoints don't require authentication
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import SessionLocal
from app.models.room import Room
from app.models.Package import Package, PackageBooking, PackageBookingRoom
from app.models.booking import Booking, BookingRoom
from app.models.food_item import FoodItem
from app.models.food_category import FoodCategory
from app.models.service import Service
from app.schemas.packages import PackageOut
from app.schemas.room import RoomOut
from typing import List
from pydantic import BaseModel
from datetime import date

# Import other schemas if needed or stick to simple
router = APIRouter(prefix="/public", tags=["Public"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Schemas for Availability
class PublicRoomRef(BaseModel):
    id: int # Room ID

class PublicBookingOut(BaseModel):
    id: int
    status: str
    check_in: date
    check_out: date
    rooms: List[PublicRoomRef]
    class Config: from_attributes = True

class PublicPackageRoomRef(BaseModel):
    room_id: int # Room ID from PackageBookingRoom

class PublicPackageBookingOut(BaseModel):
    id: int
    status: str
    check_in: date
    check_out: date
    rooms: List[PublicPackageRoomRef]
    package_id: int
    class Config: from_attributes = True


# Public Rooms endpoint
@router.get("/rooms", response_model=List[RoomOut])
def get_public_rooms(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    """Get all rooms without authentication (frontend handles availability display)"""
    try:
        rooms = db.query(Room).offset(skip).limit(limit).all()
        return rooms
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching rooms: {str(e)}")

# Public Packages endpoint
@router.get("/packages", response_model=List[PackageOut])
def get_public_packages(db: Session = Depends(get_db), skip: int = 0, limit: int = 100):
    """Get all packages without authentication"""
    try:
        packages = db.query(Package).options(joinedload(Package.images)).offset(skip).limit(limit).all()
        return packages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching packages: {str(e)}")

# Public Food Items endpoint
@router.get("/food-items")
def get_public_food_items(db: Session = Depends(get_db)):
    """Get all food items without authentication"""
    try:
        food_items = db.query(FoodItem).options(
            joinedload(FoodItem.images),
            joinedload(FoodItem.category)
        ).all()
        return food_items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching food items: {str(e)}")

# Public Food Categories endpoint
@router.get("/food-categories")
def get_public_food_categories(db: Session = Depends(get_db)):
    """Get all food categories without authentication"""
    try:
        categories = db.query(FoodCategory).all()
        return categories
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching food categories: {str(e)}")

# Public Services endpoint
@router.get("/services")
def get_public_services(db: Session = Depends(get_db)):
    """Get all services without authentication"""
    try:
        services = db.query(Service).options(joinedload(Service.images)).all()
        return services
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching services: {str(e)}")

# Public Bookings Availability
@router.get("/bookings", response_model=List[PublicBookingOut])
def get_public_bookings(db: Session = Depends(get_db), skip: int = 0, limit: int = 500):
    """Get minimal booking data for availability calculation"""
    try:
        bookings = db.query(Booking).options(joinedload(Booking.booking_rooms)).offset(skip).limit(limit).all()
        # Manually construct to map booking_rooms -> rooms
        results = []
        for b in bookings:
            room_refs = []
            if b.booking_rooms:
                for br in b.booking_rooms:
                    if br.room_id:
                         room_refs.append(PublicRoomRef(id=br.room_id))
            
            results.append(PublicBookingOut(
                id=b.id,
                status=b.status,
                check_in=b.check_in,
                check_out=b.check_out,
                rooms=room_refs
            ))
        return results
    except Exception as e:
        print(f"Error fetching public bookings: {e}")
        return []

# Public Package Bookings Availability
@router.get("/package-bookings", response_model=List[PublicPackageBookingOut])
def get_public_package_bookings(db: Session = Depends(get_db), skip: int = 0, limit: int = 500):
    """Get minimal package booking data for availability calculation"""
    try:
        bookings = db.query(PackageBooking).options(joinedload(PackageBooking.rooms)).offset(skip).limit(limit).all()
        # Manually construct
        results = []
        for b in bookings:
            room_refs = []
            if b.rooms:
                for br in b.rooms:
                    if br.room_id:
                         room_refs.append(PublicPackageRoomRef(room_id=br.room_id))
            
            results.append(PublicPackageBookingOut(
                id=b.id,
                status=b.status,
                check_in=b.check_in,
                check_out=b.check_out,
                rooms=room_refs,
                package_id=b.package_id
            ))
        return results
    except Exception as e:
        print(f"Error fetching public package bookings: {e}")
        return []
