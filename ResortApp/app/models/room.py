from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Date, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class RoomType(Base):
    __tablename__ = "room_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    total_inventory = Column(Integer, default=0) # Capacity for booking
    base_price = Column(Float, default=0.0)
    weekend_price = Column(Float, nullable=True)
    long_weekend_price = Column(Float, nullable=True)
    holiday_price = Column(Float, nullable=True)
    adults_capacity = Column(Integer, default=2)
    children_capacity = Column(Integer, default=0)
    channel_manager_id = Column(String, nullable=True) # For future OTA sync
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True, server_default="1")
    
    # Amenities moved to type level
    air_conditioning = Column(Boolean, default=False)
    wifi = Column(Boolean, default=False)
    bathroom = Column(Boolean, default=False)
    
    # Images
    image_url = Column(String, nullable=True) # Cover image
    extra_images = Column(String, nullable=True) # JSON array of additional image URLs
    living_area = Column(Boolean, default=False)
    terrace = Column(Boolean, default=False)
    parking = Column(Boolean, default=False)
    kitchen = Column(Boolean, default=False)
    family_room = Column(Boolean, default=False)
    bbq = Column(Boolean, default=False)
    garden = Column(Boolean, default=False)
    dining = Column(Boolean, default=False)
    breakfast = Column(Boolean, default=False)
    tv = Column(Boolean, default=False)
    balcony = Column(Boolean, default=False)
    mountain_view = Column(Boolean, default=False)
    ocean_view = Column(Boolean, default=False)
    private_pool = Column(Boolean, default=False)
    hot_tub = Column(Boolean, default=False)
    fireplace = Column(Boolean, default=False)
    pet_friendly = Column(Boolean, default=False)
    wheelchair_accessible = Column(Boolean, default=False)
    safe_box = Column(Boolean, default=False)
    room_service = Column(Boolean, default=False)
    laundry_service = Column(Boolean, default=False)
    gym_access = Column(Boolean, default=False)
    spa_access = Column(Boolean, default=False)
    housekeeping = Column(Boolean, default=False)
    mini_bar = Column(Boolean, default=False)

    rooms = relationship("Room", back_populates="room_type")
    branch = relationship("Branch")

class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, nullable=False)
    room_type_id = Column(Integer, ForeignKey("room_types.id"), nullable=True)
    status = Column(String, default="Available")
    housekeeping_status = Column(String, default="Clean")
    housekeeping_updated_at = Column(DateTime)
    last_maintenance_date = Column(Date)
    
    # Relationships # Clean, Dirty, Inspecting, Repair
    image_url = Column(String, nullable=True)
    extra_images = Column(String, nullable=True) # JSON string of extra image URLs
    inventory_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)  # Link to inventory locations
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True, server_default="1")
    
    branch = relationship("Branch")

    __table_args__ = (UniqueConstraint('number', 'branch_id', name='uix_room_number_branch'),)
    
    # Relationships
    room_type = relationship("RoomType", back_populates="rooms")

    # Association (one-to-many with BookingRoom)
    booking_rooms = relationship(
        "BookingRoom",
        back_populates="room",
        cascade="all, delete-orphan"
    )

    package_booking_rooms = relationship(
        "PackageBookingRoom",
        back_populates="room",
        cascade="all, delete-orphan"
    )

    food_orders = relationship(
        "FoodOrder",
        back_populates="room"
    )
    
    # Relationship to inventory location
    inventory_location = relationship("Location", foreign_keys=[inventory_location_id])

    # --- Property Delegation to RoomType ---
    @property
    def type(self):
        return self.room_type.name if self.room_type else "Unset"

    @property
    def price(self):
        return self.room_type.base_price if self.room_type else 0.0

    # Amenities delegation
    @property
    def air_conditioning(self): return self.room_type.air_conditioning if self.room_type else False
    @property
    def wifi(self): return self.room_type.wifi if self.room_type else False
    @property
    def bathroom(self): return self.room_type.bathroom if self.room_type else False
    @property
    def living_area(self): return self.room_type.living_area if self.room_type else False
    @property
    def terrace(self): return self.room_type.terrace if self.room_type else False
    @property
    def parking(self): return self.room_type.parking if self.room_type else False
    @property
    def kitchen(self): return self.room_type.kitchen if self.room_type else False
    @property
    def family_room(self): return self.room_type.family_room if self.room_type else False
    @property
    def bbq(self): return self.room_type.bbq if self.room_type else False
    @property
    def garden(self): return self.room_type.garden if self.room_type else False
    @property
    def dining(self): return self.room_type.dining if self.room_type else False
    @property
    def breakfast(self): return self.room_type.breakfast if self.room_type else False
    @property
    def tv(self): return self.room_type.tv if self.room_type else False
    @property
    def balcony(self): return self.room_type.balcony if self.room_type else False
    @property
    def mountain_view(self): return self.room_type.mountain_view if self.room_type else False
    @property
    def ocean_view(self): return self.room_type.ocean_view if self.room_type else False
    @property
    def private_pool(self): return self.room_type.private_pool if self.room_type else False
    @property
    def hot_tub(self): return self.room_type.hot_tub if self.room_type else False
    @property
    def fireplace(self): return self.room_type.fireplace if self.room_type else False
    @property
    def pet_friendly(self): return self.room_type.pet_friendly if self.room_type else False
    @property
    def wheelchair_accessible(self): return self.room_type.wheelchair_accessible if self.room_type else False
    @property
    def safe_box(self): return self.room_type.safe_box if self.room_type else False
    @property
    def room_service(self): return self.room_type.room_service if self.room_type else False
    @property
    def laundry_service(self): return self.room_type.laundry_service if self.room_type else False
    @property
    def gym_access(self): return self.room_type.gym_access if self.room_type else False
    @property
    def spa_access(self): return self.room_type.spa_access if self.room_type else False
    @property
    def housekeeping(self): return self.room_type.housekeeping if self.room_type else False
    @property
    def mini_bar(self): return self.room_type.mini_bar if self.room_type else False

    @property
    def room_type_image_url(self): return self.room_type.image_url if self.room_type else None

    @property
    def room_type_extra_images(self): return self.room_type.extra_images if self.room_type else None

    @property
    def adults_capacity(self): return self.room_type.adults_capacity if self.room_type else 2

    @property
    def children_capacity(self): return self.room_type.children_capacity if self.room_type else 0

    def __repr__(self):
        return f"<Room id={self.id} number={self.number} status={self.status}>"
