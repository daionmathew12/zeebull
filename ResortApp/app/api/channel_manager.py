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
    
    reservation_id = payload.get("bookingID") or payload.get("bookingId")
    action = str(payload.get("action", "")).lower()
    channel_name = payload.get("channel", "OTA")
    
    if not reservation_id:
        logger.error(f"[AIOSELL WEBHOOK] Missing bookingID/bookingId in payload: {payload}")
        return Response(status_code=400, content="Missing bookingID or bookingId")
        
    # BRANCH logic -> Defaulting to standard branch 1 for sandbox integration
    branch_id = 1 
        
    if action == "book":
        return _handle_new_booking(payload, db, branch_id)
    elif action == "modify":
        return _handle_modify_booking(payload, db)
    elif action == "cancel":
        return _handle_cancel_booking(payload, db)
    else:
        logger.warning(f"[AIOSELL WEBHOOK] Unknown action: {action}")
        return {"success": True, "message": f"Ignored action {action}"}


def _map_room_type(db: Session, room_code: str, branch_id: int):
    """Helper to map Aiosell roomCode to Zeebull RoomType"""
    if not room_code:
        return None
        
    # 1. Direct ID/CM ID match
    room_type = db.query(RoomType).filter(
        RoomType.channel_manager_id == room_code, 
        RoomType.branch_id == branch_id
    ).first()
    
    # 2. Case-insensitive name match if CM ID fails
    if not room_type:
        room_type = db.query(RoomType).filter(
            RoomType.name.ilike(room_code.replace("-", " ")),
            RoomType.branch_id == branch_id
        ).first()
        
    # 3. Fuzzy fallback
    if not room_type:
        room_type = db.query(RoomType).filter(
            RoomType.name.ilike(f"%{room_code}%"),
            RoomType.branch_id == branch_id
        ).first()
        
    return room_type

def _extract_amount(payload: dict) -> float:
    """Helper to extract total amount from various Aiosell payload formats"""
    # Try root level first
    amt = payload.get("totalAmount")
    if amt is not None:
        return float(amt)
        
    # Try nested amount object
    amount_obj = payload.get("amount", {})
    amt = amount_obj.get("amountAfterTax") or amount_obj.get("amount")
    if amt is not None:
        return float(amt)
        
    return 0.0
    
def _extract_channel(payload: dict) -> str:
    """Helper to extract channel name from various Aiosell/OTA formats"""
    return (
        payload.get("channel") or 
        payload.get("channelName") or 
        payload.get("source") or 
        payload.get("segment") or 
        "OTA"
    )

def _handle_new_booking(payload: dict, db: Session, branch_id: int):
    # Check if we already have it
    res_id = payload.get("bookingID") or payload.get("bookingId")
    existing = db.query(Booking).filter(Booking.external_id == res_id).first()
    if existing:
        # If it exists, redirect to modify logic to ensure it's up to date
        return _handle_modify_booking(payload, db)
        
    guest = payload.get("guest", {})
    first_name = str(guest.get("firstName") or "").replace("None", "").strip()
    last_name = str(guest.get("lastName") or "").replace("None", "").strip()
    name = f"{first_name} {last_name}".strip() or "Aiosell Guest"
    email = guest.get("email") or payload.get("email")
    
    # Robust phone number extraction
    phone = (
        guest.get("phone") or 
        guest.get("mobile") or 
        guest.get("mobileNumber") or 
        guest.get("contactNumber") or
        payload.get("phone") or 
        payload.get("mobile") or
        payload.get("contactNumber")
    )
    
    rooms = payload.get("rooms", [])
    room_type_id = None
    if rooms:
        primary_room_data = rooms[0]
        room_code = primary_room_data.get("roomCode")
        room_type = _map_room_type(db, room_code, branch_id)
        if room_type:
            room_type_id = room_type.id
            
    # Extract Rate Plan and Price Details
    rate_plan_code = None
    room_rate = 0.0
    if rooms:
        primary = rooms[0]
        rate_plan_code = primary.get("rateplanCode")
        
        # Try to get sellRate from prices array
        prices = primary.get("prices", [])
        if prices and isinstance(prices, list):
            room_rate = float(prices[0].get("sellRate", 0))
        elif "sellingPrice" in primary:
            room_rate = float(primary.get("sellingPrice", 0))
            
    special_requests = payload.get("specialRequests") or payload.get("notes")
             
    # Parse dates
    try:
        check_in = datetime.strptime(payload.get("checkin"), "%Y-%m-%d").date()
        check_out = datetime.strptime(payload.get("checkout"), "%Y-%m-%d").date()
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
    total_adults = sum([int(r.get("occupancy", {}).get("adults", 1)) for r in rooms])
    total_children = sum([int(r.get("occupancy", {}).get("children", 0)) for r in rooms])
    
    # Extract total amount
    total_amount = _extract_amount(payload)
    
    advance_deposit = 0.0 
    if str(payload.get("pah", "True")).lower() == "false":
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
        source=_extract_channel(payload),
        external_id=res_id,
        user_id=user_id,
        branch_id=branch_id,
        status="Booked",
        num_rooms=num_rooms,
        total_amount=total_amount,
        advance_deposit=advance_deposit,
        room_rate=room_rate,
        rate_plan_code=rate_plan_code,
        special_requests=special_requests
    )
    
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    
    db_booking.display_id = format_display_id(db_booking.id, branch_id=branch_id)
    db.commit()
    
    logger.info(f"[AIOSELL WEBHOOK] Created Booking {db_booking.display_id} from {res_id}")
    return {"success": True, "booking_id": db_booking.id, "display_id": db_booking.display_id}

def _handle_modify_booking(payload: dict, db: Session):
    res_id = payload.get("bookingID") or payload.get("bookingId")
    booking = db.query(Booking).filter(Booking.external_id == res_id).first()
    
    if not booking:
        # Fallback to creation if branch_id is available (defaulting to 1 for now)
        logger.warning(f"[AIOSELL WEBHOOK] Modify for non-existent booking {res_id}. Attempting to create.")
        return _handle_new_booking(payload, db, 1)
        
    # Apply modifications
    rooms = payload.get("rooms", [])
    if rooms:
        primary = rooms[0]
        try:
            booking.check_in = datetime.strptime(payload.get("checkin"), "%Y-%m-%d").date()
            booking.check_out = datetime.strptime(payload.get("checkout"), "%Y-%m-%d").date()
            booking.num_rooms = len(rooms)
            booking.adults = sum([int(r.get("occupancy", {}).get("adults", 1)) for r in rooms])
            booking.children = sum([int(r.get("occupancy", {}).get("children", 0)) for r in rooms])
            
            # UPDATE ROOM TYPE
            room_code = primary.get("roomCode")
            room_type = _map_room_type(db, room_code, booking.branch_id)
            if room_type:
                booking.room_type_id = room_type.id
                
            # UPDATE RATE AND PRICE
            booking.rate_plan_code = primary.get("rateplanCode")
            prices = primary.get("prices", [])
            if prices and isinstance(prices, list):
                booking.room_rate = float(prices[0].get("sellRate", 0))
            elif "sellingPrice" in primary:
                booking.room_rate = float(primary.get("sellingPrice", 0))
                
            booking.special_requests = payload.get("specialRequests") or payload.get("notes")
        except Exception as e:
            logger.error(f"[AIOSELL] Error during modify extraction: {e}")
            
    # Update amount and channel
    booking.total_amount = _extract_amount(payload)
    booking.source = _extract_channel(payload)
    
    db.commit()
    logger.info(f"[AIOSELL WEBHOOK] Modified Booking {booking.display_id} from {res_id}")
    return {"success": True, "message": "Modified"}
    
    db.commit()
    logger.info(f"[AIOSELL WEBHOOK] Modified Booking {booking.display_id} from {res_id}")
    return {"success": True, "message": "Modified"}

def _handle_cancel_booking(payload: dict, db: Session):
    res_id = payload.get("bookingID") or payload.get("bookingId")
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
