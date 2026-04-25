from sqlalchemy import Column, Float, Integer, String, ForeignKey, Date, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import timezone, datetime
from app.database import Base
from .room import Room, RoomType
from .user import User

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    display_id = Column(String, index=True, nullable=True) # BK-000001
    status = Column(String, default="booked")
    guest_name = Column(String, nullable=False)
    guest_mobile = Column(String, nullable=True)
    guest_email = Column(String, nullable=True)
    check_in = Column(Date, nullable=False)
    check_out = Column(Date, nullable=False)
    checked_in_at = Column(DateTime, nullable=True)  # Actual check-in timestamp
    checked_out_at = Column(DateTime, nullable=True) # Actual check-out timestamp
    adults = Column(Integer, default=2)
    children = Column(Integer, default=0)
    id_card_image_url = Column(String, nullable=True)
    guest_photo_url = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    total_amount = Column(Float, default=0.0)
    advance_deposit = Column(Float, default=0.0)  # Advance payment made during booking
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc)) # Added
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    room_type_id = Column(Integer, ForeignKey("room_types.id"), nullable=True) # Selected Room Type
    num_rooms = Column(Integer, default=1) # Number of rooms requested
    external_id = Column(String, nullable=True) # OTA/CM ID
    
    branch = relationship("Branch")
    room_type = relationship("RoomType")

    
    # New Fields
    source = Column(String, default="Direct")  # Direct, OTA, Walk-in
    package_name = Column(String, nullable=True)  # Name of package if any
    
    is_id_verified = Column(Boolean, default=False)
    digital_signature_url = Column(String, nullable=True)
    special_requests = Column(String, nullable=True)
    preferences = Column(String, nullable=True)
    
    # Relationships
    checkout = relationship("Checkout", back_populates="booking", uselist=False)

    user = relationship("User", back_populates="bookings")
    booking_rooms = relationship(
        "BookingRoom",
        back_populates="booking",
        cascade="all, delete-orphan"
    )
    payments = relationship("Payment", back_populates="booking")

class BookingRoom(Base):
    __tablename__ = "booking_rooms"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"))
    room_id = Column(Integer, ForeignKey("rooms.id"))
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True)
    
    branch = relationship("Branch")


    booking = relationship("Booking", back_populates="booking_rooms")
    room = relationship("Room", back_populates="booking_rooms")
