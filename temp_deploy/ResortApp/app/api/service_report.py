"""
Detailed Service Usage Report
Shows services used by guests, room-wise, with location/store information
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_
from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel
from app.utils.auth import get_db, get_current_user
from app.models.user import User
from app.models.service import AssignedService, Service
from app.models.booking import Booking, BookingRoom
from app.models.Package import PackageBooking, PackageBookingRoom
from app.models.room import Room
from app.models.employee import Employee
from app.models.inventory import Location
from app.models.employee_inventory import EmployeeInventoryAssignment

router = APIRouter(prefix="/reports/services", tags=["Service Reports"])


class ServiceUsageItem(BaseModel):
    """Individual service usage record"""
    assigned_service_id: int
    service_id: int
    service_name: str
    service_description: Optional[str]
    service_charges: float
    room_id: int
    room_number: str
    location_id: Optional[int]
    location_name: Optional[str]
    location_type: Optional[str]
    guest_name: Optional[str]
    booking_id: Optional[int]
    booking_type: Optional[str]  # "booking" or "package"
    employee_id: int
    employee_name: str
    assigned_at: datetime
    last_used_at: Optional[datetime]
    status: str
    billing_status: str
    inventory_items_used: List[dict] = []
    inventory_items_returned: List[dict] = []


class ServiceUsageReport(BaseModel):
    """Complete service usage report"""
    from_date: Optional[date]
    to_date: Optional[date]
    total_services: int
    total_charges: float
    by_room: dict  # Room number -> list of services
    by_guest: dict  # Guest name -> list of services
    by_location: dict  # Location -> list of services
    services: List[ServiceUsageItem]


@router.get("/detailed-usage", response_model=ServiceUsageReport)
def get_detailed_service_usage_report(
    from_date: Optional[date] = Query(None, description="Start date for the report"),
    to_date: Optional[date] = Query(None, description="End date for the report"),
    room_number: Optional[str] = Query(None, description="Filter by specific room number"),
    guest_name: Optional[str] = Query(None, description="Filter by guest name"),
    location_id: Optional[int] = Query(None, description="Filter by location/store ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed service usage report with guest, room, and location information.
    Shows all services used, organized by room, guest, and location/store.
    """
    # Store filter parameters
    guest_name_param = guest_name
    location_id_param = location_id
    
    try:
        # Build query for assigned services
        query = db.query(AssignedService).options(
            joinedload(AssignedService.service),
            joinedload(AssignedService.employee),
            joinedload(AssignedService.room)
        )
        
        # Apply date filters
        if from_date:
            query = query.filter(AssignedService.assigned_at >= datetime.combine(from_date, datetime.min.time()))
        if to_date:
            query = query.filter(AssignedService.assigned_at <= datetime.combine(to_date, datetime.max.time()))
        
        # Apply room filter
        if room_number:
            room = db.query(Room).filter(Room.number == room_number).first()
            if room:
                query = query.filter(AssignedService.room_id == room.id)
            else:
                return ServiceUsageReport(
                    from_date=from_date,
                    to_date=to_date,
                    total_services=0,
                    total_charges=0.0,
                    by_room={},
                    by_guest={},
                    by_location={},
                    services=[]
                )
        
        assigned_services = query.order_by(AssignedService.assigned_at.desc()).all()
        
        # Get all rooms and their locations
        rooms = {r.id: r for r in db.query(Room).all()}
        
        # Get all locations
        locations = {loc.id: loc for loc in db.query(Location).all()}
        
        # Get bookings and package bookings for guest information
        all_bookings = {}
        all_package_bookings = {}
        
        # Get regular bookings
        bookings = db.query(Booking).options(
            joinedload(Booking.booking_rooms).joinedload(BookingRoom.room)
        ).all()
        for booking in bookings:
            for br in booking.booking_rooms:
                all_bookings[br.room_id] = {
                    "guest_name": booking.guest_name,
                    "booking_id": booking.id,
                    "booking_type": "booking"
                }
        
        # Get package bookings
        package_bookings = db.query(PackageBooking).options(
            joinedload(PackageBooking.rooms).joinedload(PackageBookingRoom.room)
        ).all()
        for pkg_booking in package_bookings:
            for pbr in pkg_booking.rooms:
                all_package_bookings[pbr.room_id] = {
                    "guest_name": pkg_booking.guest_name,
                    "booking_id": pkg_booking.id,
                    "booking_type": "package"
                }
        
        # Process assigned services
        services_list = []
        by_room = {}
        by_guest = {}
        by_location = {}
        total_charges = 0.0
        
        for assigned in assigned_services:
            if not assigned.service or not assigned.employee or not assigned.room:
                continue
            
            room = assigned.room
            room_location = None
            location_id = None
            location_name = None
            location_type = None
            
            # Get room's location if available
            if hasattr(room, 'inventory_location_id') and room.inventory_location_id:
                location_id = room.inventory_location_id
                room_location = locations.get(location_id)
                if room_location:
                    location_name = room_location.name
                    location_type = room_location.location_type
            
            # Get guest information
            guest_info = all_bookings.get(room.id) or all_package_bookings.get(room.id)
            guest_name = guest_info.get("guest_name") if guest_info else None
            booking_id = guest_info.get("booking_id") if guest_info else None
            booking_type = guest_info.get("booking_type") if guest_info else None
            
            # Apply guest filter if specified
            if guest_name_param:
                if not guest_name or guest_name_param.lower() not in guest_name.lower():
                    continue
            
            # Apply location filter if specified
            if location_id_param and location_id != location_id_param:
                continue
            
            # Get inventory items used
            inventory_items_used = []
            inventory_items_returned = []
            
            try:
                # Get employee inventory assignments for this service
                inv_assignments = db.query(EmployeeInventoryAssignment).filter(
                    EmployeeInventoryAssignment.assigned_service_id == assigned.id
                ).options(
                    joinedload(EmployeeInventoryAssignment.item)
                ).all()
                
                for inv_ass in inv_assignments:
                    if inv_ass.item:
                        item_data = {
                            "item_id": inv_ass.item_id,
                            "item_name": inv_ass.item.name,
                            "item_code": inv_ass.item.item_code,
                            "quantity_assigned": inv_ass.quantity_assigned,
                            "quantity_used": inv_ass.quantity_used,
                            "quantity_returned": inv_ass.quantity_returned,
                            "unit": inv_ass.item.unit or "pcs"
                        }
                        inventory_items_used.append(item_data)
                        
                        if inv_ass.quantity_returned > 0:
                            inventory_items_returned.append({
                                **item_data,
                                "returned_at": inv_ass.returned_at.isoformat() if inv_ass.returned_at else None
                            })
            except Exception as inv_error:
                print(f"[WARNING] Could not load inventory items for assigned service {assigned.id}: {inv_error}")
            
            service_item = ServiceUsageItem(
                assigned_service_id=assigned.id,
                service_id=assigned.service.id,
                service_name=assigned.service.name,
                service_description=assigned.service.description,
                service_charges=assigned.service.charges,
                room_id=room.id,
                room_number=room.number,
                location_id=location_id,
                location_name=location_name,
                location_type=location_type,
                guest_name=guest_name,
                booking_id=booking_id,
                booking_type=booking_type,
                employee_id=assigned.employee.id,
                employee_name=assigned.employee.name,
                assigned_at=assigned.assigned_at,
                last_used_at=assigned.last_used_at,
                status=assigned.status.value if hasattr(assigned.status, 'value') else str(assigned.status),
                billing_status=assigned.billing_status,
                inventory_items_used=inventory_items_used,
                inventory_items_returned=inventory_items_returned
            )
            
            services_list.append(service_item)
            total_charges += assigned.service.charges
            
            # Organize by room
            if room.number not in by_room:
                by_room[room.number] = []
            by_room[room.number].append(service_item.dict())
            
            # Organize by guest
            if guest_name:
                if guest_name not in by_guest:
                    by_guest[guest_name] = []
                by_guest[guest_name].append(service_item.dict())
            
            # Organize by location
            if location_name:
                if location_name not in by_location:
                    by_location[location_name] = []
                by_location[location_name].append(service_item.dict())
        
        return ServiceUsageReport(
            from_date=from_date,
            to_date=to_date,
            total_services=len(services_list),
            total_charges=total_charges,
            by_room=by_room,
            by_guest=by_guest,
            by_location=by_location,
            services=services_list
        )
        
    except Exception as e:
        import traceback
        print(f"[ERROR] Error generating service usage report: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

