from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from datetime import datetime
import os
import secrets
from typing import Dict, Any
import logging

from app.database import get_db
from app.models.booking import Booking, BookingRoom
from app.models.room import RoomType, Room
from app.api.booking import get_or_create_guest_user, format_display_id

logger = logging.getLogger(__name__)

router = APIRouter()

# Authenticate incoming requests from Aiosell
def verify_webhook_auth(request: Request):
    """Basic Auth checker for incoming webhooks"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
        
    expected_username = os.getenv("AIOSELL_WEBHOOK_USERNAME", "sandboxpms")
    expected_password = os.getenv("AIOSELL_WEBHOOK_PASSWORD", "sandboxpms")
    
    # Simple unsecure check for basic auth (Base64 decode in production, or just use secrets.compare_digest on header)
    import base64
    expected_b64 = base64.b64encode(f"{expected_username}:{expected_password}".encode()).decode()
    expected_auth = f"Basic {expected_b64}"
    
    if not secrets.compare_digest(auth_header, expected_auth):
        logger.warning(f"Failed webhook auth attempt. Header: {auth_header}")
        raise HTTPException(status_code=401, detail="Invalid Credentials")

@router.post("/webhook")
async def aiosell_webhook(
    request: Request,
    payload: Dict[Any, Any], 
    db: Session = Depends(get_db)
):
    """
    Inbound webhook for Aiosell Reservation Push
    Receives NEW, MODIFIED, CANCELLED reservations.
    """
    verify_webhook_auth(request)
    
    logger.info(f"[AIOSELL WEBHOOK] Received payload: {payload}")
    
    reservation_id = payload.get("reservationId")
    status = str(payload.get("status", "")).upper()
    channel_name = payload.get("channelName", "OTA")
    
    if not reservation_id:
        return Response(status_code=400, content="Missing reservationId")
        
    # BRANCH logic -> Defaulting to standard branch 1 for sandbox integration
    branch_id = 1 
        
    if status == "NEW":
        return _handle_new_booking(payload, db, branch_id)
    elif status == "MODIFIED":
        return _handle_modify_booking(payload, db)
    elif status == "CANCELLED":
        return _handle_cancel_booking(payload, db)
    else:
        logger.warning(f"[AIOSELL WEBHOOK] Unknown status: {status}")
        return {"success": True, "message": f"Ignored status {status}"}


def _handle_new_booking(payload: dict, db: Session, branch_id: int):
    # Check if we already have it
    res_id = payload.get("reservationId")
    existing = db.query(Booking).filter(Booking.external_id == res_id).first()
    if existing:
        return {"success": True, "message": "Booking already exists"}
        
    guest = payload.get("guest", {})
    first_name = guest.get("firstName", "")
    last_name = guest.get("lastName", "")
    name = f"{first_name} {last_name}".strip() or "Aiosell Guest"
    email = guest.get("email")
    phone = guest.get("phone")
    
    rooms = payload.get("rooms", [])
    if not rooms:
         return Response(status_code=400, content="No rooms array in payload")
         
    # We take the first room to define the dates and type since Zeebull handles 1 RoomType per booking softly
    primary_room_data = rooms[0]
    room_code = primary_room_data.get("roomCode")
    
    # 1. Map to Zeebull RoomType
    room_type = db.query(RoomType).filter(RoomType.channel_manager_id == room_code, RoomType.branch_id == branch_id).first()
    room_type_id = room_type.id if room_type else None
    
    # If not mapped by ID, try exact fuzzy match as fallback
    if not room_type_id:
        room_type = db.query(RoomType).filter(RoomType.name.ilike(f"%{room_code}%")).first()
        if room_type:
             room_type_id = room_type.id
             
    # Parse dates
    try:
        check_in = datetime.strptime(primary_room_data.get("checkIn"), "%Y-%m-%d").date()
        check_out = datetime.strptime(primary_room_data.get("checkOut"), "%Y-%m-%d").date()
    except Exception as e:
        logger.error(f"[AIOSELL] Date parsing error: {e}")
        return Response(status_code=400, content="Invalid date format")

    # 2. Get Guest User
    user_id = None
    try:
        if email or phone:
            user_id = get_or_create_guest_user(db, email, phone, name, branch_id)
    except Exception as e:
        logger.error(f"[AIOSELL] User creation error: {e}")
        
    num_rooms = len(rooms)
    total_adults = sum([int(r.get("adults", 1)) for r in rooms])
    total_children = sum([int(r.get("children", 0)) for r in rooms])
    
    # OVERRIDE Zeebull Dynamic Pricing -> Use exact totalAmount from Aiosell
    total_amount = float(payload.get("totalAmount", 0.0))
    advance_deposit = 0.0 # Could check if payment is collected by OTA
    if "Prepaid" in payload.get("channelName", ""):
        advance_deposit = total_amount
        
    # 3. Create Booking
    db_booking = Booking(
        guest_name=name,
        guest_mobile=phone,
        guest_email=email,
        check_in=check_in,
        check_out=check_out,
        adults=total_adults,
        children=total_children,
        room_type_id=room_type_id,
        source=payload.get("channelName", "OTA"),
        external_id=res_id,
        user_id=user_id,
        branch_id=branch_id,
        status="Booked",
        num_rooms=num_rooms,
        total_amount=total_amount,
        advance_deposit=advance_deposit
    )
    
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    
    db_booking.display_id = format_display_id(db_booking.id, branch_id=branch_id)
    db.commit()
    
    logger.info(f"[AIOSELL WEBHOOK] Created Booking {db_booking.display_id} from {res_id}")
    return {"success": True, "booking_id": db_booking.id, "display_id": db_booking.display_id}

def _handle_modify_booking(payload: dict, db: Session):
    res_id = payload.get("reservationId")
    booking = db.query(Booking).filter(Booking.external_id == res_id).first()
    
    if not booking:
        # Fallback to creating it if modification arrives for a missing booking
        logger.warning(f"[AIOSELL WEBHOOK] Modify for non-existent booking {res_id}. Discarding.")
        return {"success": False, "message": "Booking not found"}
        
    # Apply modifications
    rooms = payload.get("rooms", [])
    if rooms:
        primary = rooms[0]
        try:
            booking.check_in = datetime.strptime(primary.get("checkIn"), "%Y-%m-%d").date()
            booking.check_out = datetime.strptime(primary.get("checkOut"), "%Y-%m-%d").date()
            booking.num_rooms = len(rooms)
            booking.adults = sum([int(r.get("adults", 1)) for r in rooms])
            booking.children = sum([int(r.get("children", 0)) for r in rooms])
        except:
            pass
            
    booking.total_amount = float(payload.get("totalAmount", booking.total_amount))
    
    db.commit()
    logger.info(f"[AIOSELL WEBHOOK] Modified Booking {booking.display_id} from {res_id}")
    return {"success": True, "message": "Modified"}

def _handle_cancel_booking(payload: dict, db: Session):
    res_id = payload.get("reservationId")
    booking = db.query(Booking).filter(Booking.external_id == res_id).first()
    
    if not booking:
        return {"success": True, "message": "Already cancelled/missing"}
        
    booking.status = "Cancelled"
    
    # Try to clean up physical room links if assigned
    if booking.booking_rooms:
        for br in booking.booking_rooms:
            room = br.room
            if room and room.status == "Booked":
                room.status = "Available"
        
        # Delete links
        db.query(BookingRoom).filter(BookingRoom.booking_id == booking.id).delete()
        
    db.commit()
    logger.info(f"[AIOSELL WEBHOOK] Cancelled Booking {booking.display_id} from {res_id}")
    return {"success": True, "message": "Cancelled"}
