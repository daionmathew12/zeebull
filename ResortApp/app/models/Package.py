from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)
    booking_type = Column(String, default="room_type")  # "whole_property" or "room_type"
    room_types = Column(String, nullable=True)  # Comma-separated list of room types
    status = Column(String, default="active") # active, inactive
    
    # New fields
    theme = Column(String, nullable=True)  # Romance, Wellness, Adventure, Family, etc.
    default_adults = Column(Integer, default=2)  # Default number of adults for this package
    default_children = Column(Integer, default=0)  # Default number of children for this package
    max_stay_days = Column(Integer, nullable=True)  # Maximum number of days allowed for this package
    food_included = Column(String, nullable=True)  # Comma-separated list of included meals (e.g., "Breakfast,Lunch,Dinner")
    food_timing = Column(String, nullable=True)    # JSON string: {"Breakfast": "08:00", ...}
    complimentary = Column(String, nullable=True)  # Free inclusions

    # Relationships
    images = relationship("PackageImage", back_populates="package", cascade="all, delete-orphan")
    bookings = relationship("PackageBooking", back_populates="package")


class PackageImage(Base):
    __tablename__ = "package_images"
    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("packages.id"))
    image_url = Column(String, nullable=False)

    # Relationships
    package = relationship("Package", back_populates="images")


class PackageBooking(Base):
    __tablename__ = "package_bookings"
    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("packages.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    guest_name = Column(String, nullable=False)
    guest_email = Column(String, nullable=True)
    guest_mobile = Column(String, nullable=True)

    check_in = Column(Date, nullable=False)
    check_out = Column(Date, nullable=False)
    checked_in_at = Column(DateTime, nullable=True)  # Actual check-in timestamp
    adults = Column(Integer, default=2)
    children = Column(Integer, default=0)
    id_card_image_url = Column(String, nullable=True)
    guest_photo_url = Column(String, nullable=True)

    status = Column(String)
    total_amount = Column(Float, default=0.0) # Added for tracking package booking value
    advance_deposit = Column(Float, default=0.0)  # Advance payment made during booking
    food_preferences = Column(String, nullable=True)
    special_requests = Column(String, nullable=True)

    # Relationships
    package = relationship("Package", back_populates="bookings")
    user = relationship("User", back_populates="package_bookings")
    
    checkout = relationship("Checkout", back_populates="package_booking", uselist=False)

    rooms = relationship(
        "PackageBookingRoom",
        back_populates="package_booking",
        cascade="all, delete-orphan"
    )


class PackageBookingRoom(Base):
    __tablename__ = "package_booking_rooms"
    id = Column(Integer, primary_key=True, index=True)
    package_booking_id = Column(Integer, ForeignKey("package_bookings.id", ondelete="CASCADE"))
    room_id = Column(Integer, ForeignKey("rooms.id"))

    # Relationships
    package_booking = relationship("PackageBooking", back_populates="rooms")
    room = relationship("Room", back_populates="package_booking_rooms")
