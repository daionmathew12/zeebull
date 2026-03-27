from sqlalchemy.orm import Session
from app.models.booking import Booking, BookingRoom
from app.models.room import Room
from app.schemas.booking import BookingCreate, BookingUpdate
# Notification system removed

def create_booking(db: Session, booking_in: BookingCreate):
    booking = Booking(
        guest_name=booking_in.guest_name,
        guest_mobile=booking_in.guest_mobile,
        guest_email=booking_in.guest_email,
        check_in=booking_in.check_in,
        check_out=booking_in.check_out,
        adults=booking_in.adults,
        children=booking_in.children,
        user_id=booking_in.user_id,
    )
    db.add(booking)
    db.flush()  # Get booking.id before committing

    for room_id in booking_in.room_ids:
        # Add the link between booking and room
        db.add(BookingRoom(booking_id=booking.id, room_id=room_id))
        # Update the room's status to 'Booked'
        room_to_update = db.query(Room).filter(Room.id == room_id).first()
        if room_to_update:
            room_to_update.status = "Booked"

    db.commit()
    db.refresh(booking)
    
    # Notification system removed for performance
    
    return booking

def get_booking(db: Session, booking_id: int):
    return db.query(Booking).filter(Booking.id == booking_id).first()

def get_all_bookings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Booking).offset(skip).limit(limit).all()

def update_booking(db: Session, booking_id: int, booking_in: BookingUpdate):
    booking = get_booking(db, booking_id)
    if not booking:
        return None

    old_status = booking.status
    for field, value in booking_in.model_dump(exclude_unset=True).items():
        setattr(booking, field, value)

    db.commit()
    db.refresh(booking)
    
    # Notification system removed for performance
    
    return booking

def delete_booking(db: Session, booking_id: int):
    booking = get_booking(db, booking_id)
    if not booking:
        return None
    db.delete(booking)
    db.commit()
    return booking
