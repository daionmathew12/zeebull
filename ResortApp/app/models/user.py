from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from app.database import Base
from sqlalchemy.dialects.postgresql import ARRAY
import json

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)  # unique per branch now
    # Use Text for SQLite compatibility, JSON for PostgreSQL
    permissions = Column(Text, nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)

    users = relationship("User", back_populates="role")
    
    @property
    def permissions_list(self):
        """Convert permissions JSON string to list for Pydantic"""
        if self.permissions is None:
            return []
        try:
            return json.loads(self.permissions)
        except (json.JSONDecodeError, TypeError):
            return []


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    phone = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    role_id = Column(Integer, ForeignKey("roles.id"))
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True) # null for superadmin
    is_superadmin = Column(Boolean, default=False)
    
    branch = relationship("Branch")

    bookings = relationship("Booking", back_populates="user")
    role = relationship("Role", back_populates="users")
    package_bookings = relationship("PackageBooking", back_populates="user")
    employee = relationship("Employee", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
