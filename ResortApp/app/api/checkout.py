from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func, and_
from typing import List, Optional
from datetime import date, datetime, timedelta
import traceback
import json

def debug_log(msg: str):
    print(f"[DEBUG][CHECKOUT] {msg}")

# Assume your utility and model imports are set up correctly
from app.utils.auth import get_db, get_current_user
from app.utils.branch_scope import get_branch_id
from app.models.room import Room
from app.models.booking import Booking, BookingRoom
from app.models.Package import Package, PackageBooking, PackageBookingRoom
from app.models.user import User
from app.models.foodorder import FoodOrder, FoodOrderItem
from app.models.service import AssignedService, Service
from app.models.checkout import Checkout, CheckoutVerification, CheckoutPayment, CheckoutRequest as CheckoutRequestModel
from app.models.inventory import InventoryItem, StockIssue, StockIssueDetail, AssetMapping, AssetRegistry, WasteLog, LaundryLog, InventoryTransaction, LocationStock, Location
from app.models.service_request import ServiceRequest
from app.curd.inventory import generate_waste_log_number
from app.schemas.checkout import BillSummary, BillBreakdown, CheckoutFull, CheckoutSuccess, CheckoutRequest, InventoryCheckRequest
from app.utils.checkout_helpers import (
    calculate_late_checkout_fee, process_consumables_audit, process_asset_damage_check,
    deduct_room_consumables, trigger_linen_cycle, create_checkout_verification,
    process_split_payments, generate_invoice_number, calculate_gst_breakdown,
    calculate_consumable_charge
)
from app.utils.pricing import calculate_dynamic_booking_price

router = APIRouter(prefix="/bill", tags=["checkout"])

# IMPORTANT: To support this new logic, you must update your BillSummary schema.
# In `app/schemas/checkout.py`, please change the `room_number: str` field to:
# room_numbers: List[str]


@router.post("/checkout-request")
def create_checkout_request(
    room_number: str = Query(..., description="Room number to create checkout request for"),
    checkout_mode: str = Query("multiple", description="Checkout mode: 'single' or 'multiple'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):
    """
    Create a checkout request for inventory verification before checkout.
    """
    # Find the booking for this room
    room = db.query(Room).filter(Room.number == room_number, Room.branch_id == branch_id).first()
    if not room:
        # Fallback for trimmed mismatch or different branch_id
        room = db.query(Room).filter(func.trim(Room.number) == str(room_number).strip()).first()
        
    if not room:
        raise HTTPException(status_code=404, detail=f"Room {room_number} not found")
    
    # Find active booking
    booking_link = (db.query(BookingRoom)
                    .join(Booking)
                    .filter(BookingRoom.room_id == room.id, Booking.status.in_(['checked-in', 'checked_in', 'booked']))
                    .order_by(Booking.id.desc()).first())
    
    package_link = None
    booking = None
    is_package = False
    
    if booking_link:
        booking = booking_link.booking
    else:
        package_link = (db.query(PackageBookingRoom)
                        .join(PackageBooking)
                        .filter(PackageBookingRoom.room_id == room.id, PackageBooking.status.in_(['checked-in', 'checked_in', 'booked']))
                        .order_by(PackageBooking.id.desc()).first())
        if package_link:
            booking = package_link.package_booking
            is_package = True
    
    if not booking:
        raise HTTPException(status_code=404, detail=f"No active booking found for room {room_number}")
    
    # Determine rooms to create checking requests for
    target_rooms = []
    if checkout_mode == "single":
        target_rooms = [room]
    else:
        # Multiple mode: get all rooms in the booking
        if is_package:
            target_rooms = [link.room for link in booking.rooms]
        else:
            target_rooms = [link.room for link in booking.booking_rooms]
            
    try:
        requested_by_name = getattr(current_user, 'name', None) or getattr(current_user, 'email', None) or "system"
        primary_request = None
        
        for target_room in target_rooms:
            # Skip rooms that are already checked out
            if target_room.status == "Available":
                continue
                
            # Check if there's already a pending checkout request ONLY for this specific room
            existing_request = None
            if is_package:
                existing_request = db.query(CheckoutRequestModel).filter(
                    CheckoutRequestModel.package_booking_id == booking.id,
                    CheckoutRequestModel.room_number == target_room.number,
                    CheckoutRequestModel.status.in_(["pending", "inventory_checked"])
                ).first()
            else:
                existing_request = db.query(CheckoutRequestModel).filter(
                    CheckoutRequestModel.booking_id == booking.id,
                    CheckoutRequestModel.room_number == target_room.number,
                    CheckoutRequestModel.status.in_(["pending", "inventory_checked"])
                ).first()
                
            # Keep track of the primary request to return
            current_request = existing_request
            
            # If not exists, create it
            if not existing_request:
                new_request = CheckoutRequestModel(
                    booking_id=booking.id if not is_package else None,
                    package_booking_id=booking.id if is_package else None,
                    room_number=target_room.number,
                    guest_name=booking.guest_name,
                    status="pending",
                    requested_by=requested_by_name,
                    inventory_checked=False,
                    branch_id=branch_id
                )
                db.add(new_request)
                db.flush() # flush to get the id
                current_request = new_request
            
            if target_room.number == room_number:
                primary_request = current_request
        
        db.commit()
        
        # In case the specific room requested was already Available and no request was tracked for it
        if not primary_request:
            return {
                "message": "Checkout request(s) processed. Target room is already available.",
                "request_id": None,
                "status": "completed",
                "room_number": room_number,
                "guest_name": booking.guest_name
            }
        
        return {
            "message": "Checkout request(s) processed successfully",
            "request_id": primary_request.id,
            "status": primary_request.status,
            "room_number": room_number,
            "guest_name": booking.guest_name
        }
    except Exception as e:
        db.rollback()
        import traceback
        error_details = traceback.format_exc()
        print(f"Error creating checkout request: {error_details}")
        raise HTTPException(status_code=500, detail=f"Failed to create checkout request: {str(e)}")


@router.get("/checkout-request/{room_number}")
def get_checkout_request(
    room_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):
    """
    Get checkout request status for a room.
    """
    room = db.query(Room).filter(Room.number == room_number, Room.branch_id == branch_id).first()
    if not room:
        room = db.query(Room).filter(func.trim(Room.number) == str(room_number).strip()).first()
        
    if not room:
        raise HTTPException(status_code=404, detail=f"Room {room_number} not found")
    
    # Find active booking
    booking_link = (db.query(BookingRoom)
                    .join(Booking)
                    .filter(BookingRoom.room_id == room.id, Booking.status.in_(['checked-in', 'checked_in', 'booked']), Booking.branch_id == branch_id)
                    .order_by(Booking.id.desc()).first())
    
    package_link = None
    booking = None
    is_package = False
    
    if booking_link:
        booking = booking_link.booking
    else:
        package_link = (db.query(PackageBookingRoom)
                        .join(PackageBooking)
                        .filter(PackageBookingRoom.room_id == room.id, PackageBooking.status.in_(['checked-in', 'checked_in', 'booked']), PackageBooking.branch_id == branch_id)
                        .order_by(PackageBooking.id.desc()).first())
        if package_link:
            booking = package_link.package_booking
            is_package = True
    
    if not booking:
        return {"exists": False, "status": None}
    
    # Find checkout request for this specific room to use its ID for the modal
    checkout_request = None
    all_requests = []
    
    if is_package:
        all_requests = db.query(CheckoutRequestModel).filter(
            CheckoutRequestModel.package_booking_id == booking.id
        ).order_by(CheckoutRequestModel.id.desc()).all()
    else:
        all_requests = db.query(CheckoutRequestModel).filter(
            CheckoutRequestModel.booking_id == booking.id
        ).order_by(CheckoutRequestModel.id.desc()).all()
        
    if not all_requests:
        return {"exists": False, "status": None}
        
    # Find the specific request for the queried room
    for req in all_requests:
        if req.room_number == room.number:
            checkout_request = req
            break
            
    if not checkout_request:
        return {"exists": False, "status": None}
        
    # Calculate aggregate status
    # In multiple mode, if ANY request is not completed (or not inventory_checked), the booking is pending verified
    aggregate_status = checkout_request.status
    aggregate_inventory_checked = checkout_request.inventory_checked
    
    for req in all_requests:
        if req.status != "completed" or not req.inventory_checked:
            aggregate_status = "pending"
            aggregate_inventory_checked = False
            break
            
    return {
        "exists": True,
        "request_id": checkout_request.id,
        "status": aggregate_status,
        "inventory_checked": aggregate_inventory_checked,
        "inventory_checked_by": checkout_request.inventory_checked_by,
        "inventory_checked_at": checkout_request.inventory_checked_at.isoformat() if checkout_request.inventory_checked_at else None,
        "inventory_notes": checkout_request.inventory_notes,
        "requested_at": checkout_request.requested_at.isoformat() if checkout_request.requested_at else None,
        "requested_by": checkout_request.requested_by,
        "employee_id": checkout_request.employee_id,
        "employee_name": checkout_request.employee.name if checkout_request.employee else None
    }


@router.put("/checkout-request/{request_id}/status")
def update_checkout_request_status(
    request_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):
    """
    Update checkout request status directly.
    Allowed transitions: pending -> in_progress/inventory_checked/completed
    """
    checkout_request = db.query(CheckoutRequestModel).filter(CheckoutRequestModel.id == request_id).first()
    if not checkout_request:
        raise HTTPException(status_code=404, detail="Checkout request not found")
    
    valid_statuses = ["pending", "in_progress", "inventory_checked", "completed", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    
    # Update status
    checkout_request.status = status
    
    # If moving to completed, mark inventory as checked
    if status == "completed":
        checkout_request.inventory_checked = True
        checkout_request.inventory_checked_by = getattr(current_user, 'name', None) or getattr(current_user, 'email', None) or "system"
        checkout_request.inventory_checked_at = datetime.utcnow()
        checkout_request.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(checkout_request)
    
    return {
        "message": f"Checkout request status updated to {status}",
        "request_id": checkout_request.id,
        "status": checkout_request.status,
        "inventory_checked": checkout_request.inventory_checked
    }



@router.put("/checkout-request/{request_id}/assign")
def assign_employee_to_checkout_request(
    request_id: int,
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):
    """
    Assign an employee to a checkout request.
    """
    from app.models.employee import Employee
    
    checkout_request = db.query(CheckoutRequestModel).filter(CheckoutRequestModel.id == request_id).first()
    if not checkout_request:
        raise HTTPException(status_code=404, detail="Checkout request not found")
    
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    checkout_request.employee_id = employee_id
    checkout_request.status = "in_progress"
    
    db.commit()
    db.refresh(checkout_request)
    
    return {
        "message": "Employee assigned successfully",
        "request_id": checkout_request.id,
        "employee_id": checkout_request.employee_id,
        "employee_name": employee.name,
        "status": checkout_request.status
    }


@router.get("/checkout-request/{request_id}/inventory-details")
def get_checkout_request_inventory_details(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):
    checkout_request = db.query(CheckoutRequestModel).filter(CheckoutRequestModel.id == request_id).first()
    if not checkout_request:
        raise HTTPException(status_code=404, detail="Checkout request not found")

    # Only fetch the single room associated with this specific check-out request
    room = db.query(Room).filter(Room.number == checkout_request.room_number).first()
    if room:
        rooms = [room]
    else:
        debug_log(f"No room found for request {request_id}")
        raise HTTPException(status_code=404, detail=f"No room found for this checkout request")
    
    all_items_list = []
    all_fixed_assets = []
    room_details = []

    from app.curd import inventory as inventory_crud

    for room in rooms:
        # Get inventory items for the room location
        if not room.inventory_location_id:
            debug_log(f"Room {room.number} has NO Inventory Location ID")
            room_details.append({
                "room_number": room.number,
                "items": [],
                "message": "No inventory location assigned to this room"
            })
            continue
        
        # Get location items using the inventory API endpoint logic
        location = db.query(Location).filter(Location.id == room.inventory_location_id).first()
        if not location:
            debug_log(f"Location obj not found for ID {room.inventory_location_id}")
            continue
        
        try:
            location_id = location.id
            debug_log(f"Processing Room {room.number} using Location {location.name} (ID: {location_id})")
            
            # 1. Get items from LocationStock (Primary Source)
            location_stocks = db.query(LocationStock).filter(
                LocationStock.location_id == location_id,
                LocationStock.quantity > 0
            ).all()

            # 2. Get items assigned to this location via asset mappings
            asset_mappings = db.query(AssetMapping).filter(
                AssetMapping.location_id == location_id,
                AssetMapping.is_active == True
            ).all()
            
            # 3. Get items from asset registry
            asset_registry = db.query(AssetRegistry).filter(
                AssetRegistry.current_location_id == location_id
            ).all()
            
            # Combine all items for THIS room
            room_items_dict = {}
            
            # Process LocationStock
            for stock in location_stocks:
                item = stock.item
                if not item: continue
                
                # Fetch category for metadata
                category = inventory_crud.get_category_by_id(db, item.category_id)
                
                # Check for permanent mapping
                permanently_mapped_qty = 0.0
                permanent_mapping = db.query(AssetMapping).filter(
                    AssetMapping.location_id == location_id,
                    AssetMapping.item_id == item.id,
                    AssetMapping.is_active == True
                ).first()
                if permanent_mapping:
                    permanently_mapped_qty = float(permanent_mapping.quantity or 1)
                
                # Get relevant stock issues for this booking
                booking_start = None
                if checkout_request.booking:
                    booking_start = checkout_request.booking.checked_in_at or checkout_request.booking.check_in
                elif checkout_request.package_booking:
                    booking_start = checkout_request.package_booking.checked_in_at or checkout_request.package_booking.check_in
                
                issue_details_query = db.query(StockIssueDetail).join(StockIssue).filter(
                    StockIssue.destination_location_id == location_id,
                    StockIssueDetail.item_id == item.id
                )
                if booking_start:
                    issue_details_query = issue_details_query.filter(StockIssue.issue_date >= booking_start)
                issue_details = issue_details_query.order_by(StockIssue.issue_date.desc()).all()
                
                current_stock_qty = float(stock.quantity)
                issued_stock_qty = max(0, current_stock_qty - permanently_mapped_qty)
                
                good_issues = [d for d in issue_details if not getattr(d, 'is_damaged', False)]
                good_rented_issues = [d for d in good_issues if (d.rental_price and d.rental_price > 0)]
                total_rented_need = sum(float(d.issued_quantity) for d in good_rented_issues)
                
                rented_stock_qty = min(issued_stock_qty, total_rented_need)
                standard_stock_qty = max(0, issued_stock_qty - rented_stock_qty)
                
                is_asset_type = ((category and category.is_asset_fixed) or item.is_asset_fixed or item.track_laundry_cycle or (not item.is_sellable_to_guest and not item.is_perishable))

                def process_batch_internal(qty, issues, key_suffix, is_rent_split, force_payable_suffix=False, room_number=""):
                    if qty <= 0: return
                    complimentary_qty = 0.0
                    payable_qty = 0.0
                    remaining = qty
                    idx = 0
                    while remaining > 0:
                        attributed = 0
                        if idx < len(issues):
                            detail = issues[idx]
                            issued = float(detail.issued_quantity)
                            attributed = min(remaining, issued)
                            is_payable_issue = getattr(detail, 'is_payable', False)
                            if not is_payable_issue and detail.notes and ("payable" in detail.notes.lower() and "true" in detail.notes.lower()):
                                is_payable_issue = True
                            if is_payable_issue: payable_qty += attributed
                            else: complimentary_qty += attributed
                            idx += 1
                        else:
                            attributed = remaining
                            complimentary_qty += attributed
                        remaining -= attributed

                    price_per_unit = item.selling_price or item.unit_price or 0.0
                    final_charge_price = price_per_unit
                    if is_rent_split:
                        if issues and len(issues) > 0:
                             final_charge_price = getattr(issues[0], 'rental_price', 0.0) or 0.0
                        else:
                             final_charge_price = item.rental_price or 0.0

                    key = f"item_{item.id}_{room_number}{key_suffix}"
                    display_name = item.name
                    if is_asset_type:
                        if is_rent_split: display_name += " (Rented)"
                    else:
                        if force_payable_suffix or payable_qty > 0: display_name += " (Payable)"
                        else: display_name += " (Complimentary)"

                    is_fixed = is_asset_type
                    is_rentable_flag = is_rent_split
                    is_consumable = not is_asset_type or any(kw in (item.name or "").lower() for kw in ["water", "coke", "cola", "chip", "snack", "drink", "beverage", "juice", "soda", "biscuit", "cookie"])
                    if is_consumable:
                         is_fixed = False
                         is_rentable_flag = False
                         
                    room_items_dict[key] = {
                        "id": item.id,
                        "item_id": item.id,
                        "item_name": display_name,
                        "room_number": room_number,
                        "current_stock": qty,
                        "allocated_stock": qty,
                        "complimentary_qty": complimentary_qty,
                        "payable_qty": payable_qty,
                        "unit": item.unit,
                        "charge_per_unit": final_charge_price,
                        "replacement_cost": price_per_unit,
                        "is_fixed_asset": is_fixed,
                        "track_laundry_cycle": (item.track_laundry_cycle if not is_consumable else False),
                        "is_rentable": is_rentable_flag,
                        "is_payable": payable_qty > 0,
                        "complimentary_limit": item.complimentary_limit or 0
                    }

                if permanently_mapped_qty > 0:
                    key = f"asset_mapped_{item.id}_{room.number}"
                    room_items_dict[key] = {
                        "id": item.id,
                        "item_id": item.id,
                        "item_name": item.name + " (Fixed)",
                        "room_number": room.number,
                        "current_stock": permanently_mapped_qty,
                        "allocated_stock": permanently_mapped_qty,
                        "complimentary_qty": permanently_mapped_qty,
                        "unit": item.unit,
                        "charge_per_unit": item.selling_price or item.unit_price or 0,
                        "replacement_cost": item.selling_price or item.unit_price or 0,
                        "is_fixed_asset": True,
                        "track_laundry_cycle": item.track_laundry_cycle,
                        "is_rentable": False,
                        "is_payable": False
                    }
                
                if is_asset_type:
                    if rented_stock_qty > 0: process_batch_internal(rented_stock_qty, good_rented_issues, "_rented", True, room_number=room.number)
                    if standard_stock_qty > 0: process_batch_internal(standard_stock_qty, good_issues, "", False, room_number=room.number)
                else:
                    payable_good_issues = [d for d in good_issues if getattr(d, 'is_payable', False)]
                    comp_good_issues = [d for d in good_issues if not getattr(d, 'is_payable', False)]
                    total_payable_need = sum(float(d.issued_quantity) for d in payable_good_issues)
                    payable_in_stock = min(issued_stock_qty, total_payable_need)
                    comp_in_stock = max(0, issued_stock_qty - payable_in_stock)
                    if payable_in_stock > 0: process_batch_internal(payable_in_stock, payable_good_issues, "_payable", True, force_payable_suffix=True, room_number=room.number)
                    if comp_in_stock > 0: process_batch_internal(comp_in_stock, comp_good_issues, "", False, room_number=room.number)

            # Process Asset Registry
            for asset in asset_registry:
                item = asset.item
                if item:
                    key = f"registry_{asset.id}_{room.number}"
                    room_items_dict[key] = {
                        "id": item.id, "item_id": item.id, "item_name": item.name, "room_number": room.number,
                        "current_stock": 1, "allocated_stock": 1, "is_fixed_asset": True, "replacement_cost": item.unit_price or 0
                    }

            items_list = list(room_items_dict.values())
            fixed_assets = [it for it in items_list if it.get('is_fixed_asset')]
            
            all_items_list.extend(items_list)
            all_fixed_assets.extend(fixed_assets)
            
            room_details.append({
                "room_number": room.number,
                "items": items_list,
                "fixed_assets": fixed_assets,
                "location_name": location.name
            })

        except Exception as e:
            debug_log(f"Error processing room {room.number}: {str(e)}")
            continue

    return {
        "room_number": checkout_request.room_number,
        "guest_name": checkout_request.guest_name,
        "items": all_items_list,
        "fixed_assets": all_fixed_assets,
        "room_details": room_details
    }


@router.post("/checkout-request/{request_id}/check-inventory")
async def handleCompleteCheckoutRequest(
    request_id: int,
    payload: InventoryCheckRequest, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):
    """
    Mark inventory as checked and complete the checkout request.
    """
    
    checkout_request = db.query(CheckoutRequestModel).filter(CheckoutRequestModel.id == request_id).first()
    if not checkout_request:
        raise HTTPException(status_code=404, detail="Checkout request not found")
    
    if checkout_request.status == "cancelled":
        raise HTTPException(status_code=400, detail="Cannot check inventory for a cancelled request")
    
    checkout_request.inventory_checked = True
    checkout_request.inventory_checked_by = getattr(current_user, 'name', None) or getattr(current_user, 'email', None) or "system"
    checkout_request.inventory_checked_at = datetime.utcnow()
    checkout_request.inventory_notes = payload.inventory_notes
    
    # Store inventory data and calculate charges for missing items
    total_missing_charges = 0.0
    inventory_data_with_charges = []
    missing_items_details = []
    
    from app.models.inventory import InventoryItem, LocationStock, InventoryTransaction, AssetMapping, StockIssueDetail, StockIssue, LaundryLog, Location, AssetRegistry, WasteLog
    from app.models.service_request import ServiceRequest
    from sqlalchemy import or_, func
    from sqlalchemy.orm import joinedload

    if payload.items:
        for item in payload.items:
            item_dict = item.dict()
            
            # Fetch Inventory Item
            inv_item = db.query(InventoryItem).options(joinedload(InventoryItem.category)).filter(InventoryItem.id == item.item_id).first()
            if not inv_item:
                debug_log(f"[CHECKOUT ERROR] Item ID {item.item_id} not found. Skipping.")
                continue

            # Identify Target Room for this item
            target_room_number = str(getattr(item, 'room_number', None) or checkout_request.room_number).strip()
            
            room_obj = db.query(Room).filter(Room.number == target_room_number, Room.branch_id == branch_id).first()
            if not room_obj:
                room_obj = db.query(Room).filter(func.trim(Room.number) == target_room_number, Room.branch_id == branch_id).first()
            if not room_obj:
                # Last resort: global search by number without branch (as done in asset_damages loop)
                room_obj = db.query(Room).filter(func.trim(Room.number) == target_room_number).first()

            if not room_obj:
                debug_log(f"[CHECKOUT ERROR] Room '{target_room_number}' not found globally.")
                continue
            
            if not room_obj.inventory_location_id:
                debug_log(f"[CHECKOUT ERROR] Room '{target_room_number}' has no inventory_location_id.")
                continue

            room_loc_id = room_obj.inventory_location_id
            
            # Helper flags
            is_fixed_asset = getattr(inv_item, 'is_asset_fixed', False)
            if not is_fixed_asset and inv_item.category and getattr(inv_item.category, 'is_asset_fixed', False):
                is_fixed_asset = True
                
            # Use frontend flags as primary truth for split logic
            is_mapped_asset = item.is_fixed_asset and not item.is_rentable
            is_rental = item.is_rentable
            
            # Fallback check for mapped assets
            if not is_mapped_asset:
                existing_mapping = db.query(AssetMapping).filter(
                    AssetMapping.location_id == room_loc_id,
                    AssetMapping.item_id == item.item_id,
                    AssetMapping.is_active == True
                ).first()
                if existing_mapping:
                    is_mapped_asset = True

            # RECONCILIATION LOGIC
            room_stock_record = db.query(LocationStock).filter(
                LocationStock.location_id == room_loc_id,
                LocationStock.item_id == item.item_id
            ).first()

            allocated_stock = float(item.allocated_stock or 0.0)
            if allocated_stock == 0:
                if room_stock_record:
                    allocated_stock = float(room_stock_record.quantity)
                else:
                    # Fallback: Check StockIssueDetail if room_stock record is missing
                    # IMPROVED: Only sum issues from the current booking period
                    booking_start = getattr(booking, 'checked_in_at', None) or (booking.check_in if booking else datetime.utcnow())
                    if isinstance(booking_start, date) and not isinstance(booking_start, datetime):
                        booking_start = datetime.combine(booking_start, datetime.min.time())
                        
                    issued_qty = db.query(func.sum(StockIssueDetail.issued_quantity)).join(StockIssue).filter(
                        StockIssue.destination_location_id == room_loc_id,
                        StockIssueDetail.item_id == item.item_id,
                        StockIssue.issue_date >= booking_start
                    ).scalar() or 0.0
                    allocated_stock = float(issued_qty)
                    
                    # ALSO: Pre-calculate total rental charge for this item in this room
                    actual_rental_charge_base = db.query(func.sum(StockIssueDetail.issued_quantity * StockIssueDetail.rental_price)).join(StockIssue).filter(
                        StockIssue.destination_location_id == room_loc_id,
                        StockIssueDetail.item_id == item.item_id,
                        StockIssueDetail.rental_price > 0,
                        StockIssue.issue_date >= booking_start
                    ).scalar() or 0.0
                    item_rental_charge_base = float(actual_rental_charge_base)

            used_qty = float(item.used_qty or 0.0)
            missing_qty = float(item.missing_qty or 0.0)
            damage_qty = float(getattr(item, 'damage_qty', 0.0) or 0.0)
            
            # Fix NameError: Define total_lost
            total_lost = used_qty + missing_qty + damage_qty
            
            # 3. Handle Returns (Unused pieces or rental items to be returned)
            # Removed 'if not is_mapped_asset:' to allow returning extra units of mapped assets
            effective_allocated = allocated_stock
            
            # Fallback: if allocated_stock=0 but item is rentable, query issued qty directly
            if effective_allocated == 0 and is_rental:
                issued_total = db.query(func.sum(StockIssueDetail.issued_quantity)).join(StockIssue).filter(
                    StockIssue.destination_location_id == room_loc_id,
                    StockIssueDetail.item_id == item.item_id
                ).scalar() or 0.0
                effective_allocated = float(issued_total)
            
            # Calculate unused qty BEFORE we potentially modify room_stock_record for total_lost
            # unused_qty = distributed stock that wasn't lost/consumed/damaged
            unused_qty = max(0, effective_allocated - total_lost)
            
            # Now perform stock deductions for room
            if total_lost > 0 and room_stock_record:
                room_stock_record.quantity = max(0, float(room_stock_record.quantity) - total_lost)
                room_stock_record.last_updated = datetime.utcnow()

            if unused_qty > 0:
                # Deduct unused from room stock as well (it's moving out)
                if room_stock_record:
                    room_stock_record.quantity = max(0, float(room_stock_record.quantity) - unused_qty)
                    room_stock_record.last_updated = datetime.utcnow()
                
                target_return_loc_id = item.return_location_id
                if not target_return_loc_id:
                    # Fallback to Warehouse or first active store
                    fallback_loc = db.query(Location).filter(
                        (Location.name.ilike('%warehouse%')) | (Location.location_type == 'WAREHOUSE'),
                        Location.is_active == True,
                        Location.branch_id == branch_id
                    ).first()
                    if not fallback_loc:
                        fallback_loc = db.query(Location).filter(Location.is_active == True, Location.branch_id == branch_id).first()
                    
                    if fallback_loc:
                        target_return_loc_id = fallback_loc.id
                
                # Handle Laundry flow
                if item.is_laundry and target_return_loc_id:
                    laundry_entry = LaundryLog(
                        item_id=item.item_id,
                        source_location_id=room_loc_id,
                        room_number=target_room_number,
                        quantity=unused_qty,
                        status="Incomplete Washing",
                        sent_at=datetime.utcnow(),
                        created_by=current_user.id,
                        notes=f"Checkout RM{target_room_number}",
                        branch_id=branch_id
                    )
                    db.add(laundry_entry)
                    
                    if item.request_replacement:
                        new_sr = ServiceRequest(
                            room_id=room_obj.id,
                            request_type="replenishment",
                            description=f"Replacement for {inv_item.name} (sent to laundry from RM{target_room_number})",
                            status="pending",
                            created_at=datetime.utcnow(),
                            branch_id=branch_id
                        )
                        db.add(new_sr)

                # Update Target Location Stock
                if target_return_loc_id:
                    dest_stock = db.query(LocationStock).filter(
                        LocationStock.location_id == target_return_loc_id,
                        LocationStock.item_id == item.item_id
                    ).first()
                    if dest_stock:
                        dest_stock.quantity = float(dest_stock.quantity) + unused_qty
                        dest_stock.last_updated = datetime.utcnow()
                    else:
                        db.add(LocationStock(
                            location_id=target_return_loc_id,
                            item_id=item.item_id,
                            quantity=unused_qty,
                            last_updated=datetime.utcnow(),
                            branch_id=branch_id
                        ))
                    
                    # ADDED: Transaction for returned items
                    return_txn = InventoryTransaction(
                        item_id=item.item_id,
                        transaction_type="transfer", # Fixed from transfer_in
                        quantity=unused_qty,
                        unit_price=inv_item.unit_price or 0.0,
                        total_amount=0.0,
                        reference_number=f"CHKINV-RET-{checkout_request.id}",
                        notes=f"Returned at checkout - Room {target_room_number}",
                        created_by=current_user.id,
                        source_location_id=room_loc_id,
                        destination_location_id=target_return_loc_id,
                        branch_id=branch_id
                    )
                    db.add(return_txn)
                    
                    # UPDATE StockIssueDetail to reflect return
                    # This prevents the item from showing as "Issued" in the Room Stock UI
                    active_issue = db.query(StockIssueDetail).join(StockIssue).filter(
                        StockIssue.destination_location_id == room_loc_id,
                        StockIssueDetail.item_id == item.item_id,
                        StockIssueDetail.issued_quantity > 0
                    ).order_by(StockIssue.issue_date.desc()).first()
                    
                    if active_issue:
                        active_issue.issued_quantity = max(0, float(active_issue.issued_quantity) - unused_qty)
                        db.add(active_issue)

                    # Update global current_stock if returning to warehouse-like location
                    return_loc = db.query(Location).filter(Location.id == target_return_loc_id).first()
                    if return_loc and return_loc.location_type:
                        loc_type = return_loc.location_type.upper()
                        if loc_type in ["WAREHOUSE", "CENTRAL_WAREHOUSE", "BRANCH_STORE", "REPAIR", "LAUNDRY"]:
                            inv_item.current_stock = (inv_item.current_stock or 0) + unused_qty
                            db.add(inv_item)
                    
                # Handle Waste and Damages
                if damage_qty > 0:
                    if getattr(item, 'is_rentable', False):
                        # Mark matching rental issue as damaged
                        rental_issue_to_mark = db.query(StockIssueDetail).join(StockIssue).filter(
                            StockIssue.destination_location_id == room_loc_id,
                            StockIssueDetail.item_id == item.item_id,
                            or_(StockIssueDetail.rental_price > 0, StockIssueDetail.is_payable == True)
                        ).order_by(StockIssue.issue_date.desc()).first()
                        if rental_issue_to_mark:
                            rental_issue_to_mark.is_damaged = True
                            rental_issue_to_mark.damage_notes = f"Reported at checkout #{checkout_request.id}"
                            db.add(rental_issue_to_mark)
                    else:
                        registry_item = db.query(AssetRegistry).filter(
                            AssetRegistry.item_id == item.item_id,
                            AssetRegistry.current_location_id == room_loc_id
                        ).first()
                        if registry_item:
                            registry_item.status = "damaged"
                            db.add(registry_item)
                        
                        mapping_to_mark = db.query(AssetMapping).filter(
                            AssetMapping.location_id == room_loc_id,
                            AssetMapping.item_id == item.item_id,
                            AssetMapping.is_active == True
                        ).first()
                        if mapping_to_mark:
                            note_to_add = f" [Reported Damaged at Checkout #{checkout_request.id}]"
                            if note_to_add not in (mapping_to_mark.notes or ""):
                                mapping_to_mark.notes = (mapping_to_mark.notes or "") + note_to_add
                                db.add(mapping_to_mark)

            # Deactivate Asset Mapping ONLY if the mapped units themselves are damaged
            if is_fixed_asset and room_stock_record and damage_qty > 0:
                mapping_to_deactivate = db.query(AssetMapping).filter(
                    AssetMapping.location_id == room_loc_id,
                    AssetMapping.item_id == item.item_id,
                    AssetMapping.is_active == True
                ).first()

                if mapping_to_deactivate:
                    if mapping_to_deactivate.quantity > int(damage_qty):
                        mapping_to_deactivate.quantity -= int(damage_qty)
                    else:
                        mapping_to_deactivate.is_active = False
                    db.add(mapping_to_deactivate)

            # 4. Calculate Complimentary Limit
            calculated_limit = 0
            booking = None
            if checkout_request.booking_id:
                booking = db.query(Booking).filter(Booking.id == checkout_request.booking_id).first()
            elif checkout_request.package_booking_id:
                booking = db.query(PackageBooking).filter(PackageBooking.id == checkout_request.package_booking_id).first()
            
            if booking:
                booking_start = getattr(booking, 'checked_in_at', None) or booking.check_in
                comp_issued_qty = (db.query(func.sum(StockIssueDetail.issued_quantity))
                    .join(StockIssue)
                    .filter(
                        StockIssue.destination_location_id == room_loc_id,
                        StockIssueDetail.item_id == item.item_id,
                        StockIssue.issue_date >= booking_start,
                        or_(StockIssueDetail.is_payable == False, StockIssueDetail.is_payable == None)
                    )
                    .scalar()) or 0.0
                calculated_limit = float(comp_issued_qty)
            else:
                calculated_limit = float(inv_item.complimentary_limit or 0.0)

            item_dict['complimentary_limit'] = calculated_limit
            limit = calculated_limit

            # 5. Calculate charges for used items
            # For rentals, we charge even if used_qty is 0 (charge for the presence in room)
            usage_charge = 0.0
            price_to_use = 0.0
            actual_chargeable_qty = 0.0
            
            if used_qty > 0 or is_rental:
                if is_rental:
                    # Rental logic: Charge for what was issued and not lost/damaged
                    actual_chargeable_qty = max(0, allocated_stock - missing_qty - damage_qty)
                    
                    # PRIORITY: Calculate this BEFORE we potentially modify active_issue.issued_quantity later
                    rental_issue = db.query(StockIssueDetail).join(StockIssue).filter(
                        StockIssue.destination_location_id == room_loc_id,
                        StockIssueDetail.item_id == item.item_id,
                        StockIssueDetail.rental_price > 0
                    ).order_by(StockIssue.issue_date.desc()).first()
                    
                    if rental_issue:
                        # Calculate stay_days
                        stay_days = 1
                        if booking:
                            eff_checkout = checkout_request.completed_at or datetime.utcnow()
                            booking_checkin = getattr(booking, 'checked_in_at', None) or booking.check_in
                            if isinstance(booking_checkin, datetime):
                                booking_checkin = booking_checkin.date()
                            stay_days = max(1, (eff_checkout.date() - booking_checkin).days)
                        
                        # Sum up all rental prices for this item for the current booking
                        actual_rental_sum = db.query(func.sum(StockIssueDetail.issued_quantity * StockIssueDetail.rental_price)).join(StockIssue).filter(
                            StockIssue.destination_location_id == room_loc_id,
                            StockIssueDetail.item_id == item.item_id,
                            StockIssueDetail.rental_price > 0,
                            StockIssue.issue_date >= (getattr(booking, 'checked_in_at', None) or booking.check_in)
                        ).scalar() or 0.0
                        
                        price_to_use = float(rental_issue.rental_price)
                        if actual_rental_sum > 0:
                            usage_charge = float(actual_rental_sum) * stay_days
                        else:
                            usage_charge = actual_chargeable_qty * price_to_use * stay_days
                    else:
                        # Fallback to selling price if no rental issue found but marked as rentable
                        usage_charge, price_to_use, _ = calculate_consumable_charge(inv_item, used_qty if used_qty > 0 else actual_chargeable_qty, limit_from_audit=limit)
                else:
                    # Standard consumable logic
                    usage_charge, price_to_use, actual_chargeable_qty = calculate_consumable_charge(inv_item, used_qty, limit_from_audit=limit)

                if usage_charge > 0:
                    item_dict['total_charge'] = usage_charge
                    item_dict['payable_usage_qty'] = actual_chargeable_qty
                    item_dict['unit_price'] = price_to_use 
                else:
                    item_dict['total_charge'] = 0.0
                    item_dict['payable_usage_qty'] = 0.0
                    item_dict['unit_price'] = price_to_use

            # 6. Calculate Damage / Missing Charge (BAD CHARGE)
            total_bad_qty = missing_qty + damage_qty
            if total_bad_qty > 0:
                price_base = float(inv_item.selling_price or inv_item.unit_price or 0.0)
                if price_base > 0:
                    gst_rate = float(inv_item.gst_rate or 0.0)
                    if inv_item.selling_price and inv_item.selling_price > 0:
                        unit_charge_with_tax = float(inv_item.selling_price)
                    else:
                        gst_multiplier = 1.0 + (gst_rate / 100.0)
                        unit_charge_with_tax = price_base * gst_multiplier
                    
                    total_bad_charge = total_bad_qty * unit_charge_with_tax
                    item_dict['missing_item_charge'] = total_bad_charge
                    item_dict['damage_charge'] = total_bad_charge 
                    item_dict['unit_price'] = unit_charge_with_tax
                    item_dict['damage_qty'] = damage_qty
                    item_dict['missing_qty'] = missing_qty
                    
                    total_missing_charges += total_bad_charge
                    
                    missing_items_details.append({
                        "item_name": inv_item.name,
                        "item_code": inv_item.item_code,
                        "missing_qty": missing_qty,
                        "damage_qty": damage_qty,
                        "unit_price": unit_charge_with_tax,
                        "total_charge": total_bad_charge,
                        "type": "damaged" if damage_qty > 0 else "missing",
                        "room_number": target_room_number
                    })

            # Now perform stock deductions and returns for room AFTER calculating charges
            # 3. Handle Returns (Unused pieces or rental items to be returned)
            effective_allocated = allocated_stock
            if effective_allocated == 0 and is_rental:
                 effective_allocated = float(actual_chargeable_qty or 0)
            
            unused_qty = max(0, effective_allocated - total_lost)
            
            if total_lost > 0 and room_stock_record:
                room_stock_record.quantity = max(0, float(room_stock_record.quantity) - total_lost)
                room_stock_record.last_updated = datetime.utcnow()

            if unused_qty > 0:
                if room_stock_record:
                    room_stock_record.quantity = max(0, float(room_stock_record.quantity) - unused_qty)
                    room_stock_record.last_updated = datetime.utcnow()
                
                target_return_loc_id = item.return_location_id
                if not target_return_loc_id:
                    # Fallback loc search logic...
                    fallback_loc = db.query(Location).filter(
                        (Location.name.ilike('%warehouse%')) | (Location.location_type == 'WAREHOUSE'),
                        Location.is_active == True, Location.branch_id == branch_id
                    ).first()
                    if not fallback_loc: fallback_loc = db.query(Location).filter(Location.is_active == True, Location.branch_id == branch_id).first()
                    if fallback_loc: target_return_loc_id = fallback_loc.id
                
                if target_return_loc_id:
                    # Laundry / Stock Update / Transaction / Issue Update
                    dest_stock = db.query(LocationStock).filter(LocationStock.location_id == target_return_loc_id, LocationStock.item_id == item.item_id).first()
                    if dest_stock:
                        dest_stock.quantity = float(dest_stock.quantity) + unused_qty
                    else:
                        db.add(LocationStock(location_id=target_return_loc_id, item_id=item.item_id, quantity=unused_qty, last_updated=datetime.utcnow(), branch_id=branch_id))
                    
                    # Update StockIssueDetail (THIS causes later lookups to find 0 if not careful)
                    active_issue = db.query(StockIssueDetail).join(StockIssue).filter(
                        StockIssue.destination_location_id == room_loc_id,
                        StockIssueDetail.item_id == item.item_id,
                        StockIssueDetail.issued_quantity > 0
                    ).first()
                    if active_issue:
                        active_issue.issued_quantity = max(0, float(active_issue.issued_quantity) - unused_qty)
                    

            # Append the final item_dict
            inventory_data_with_charges.append(item_dict)

    # Process asset damages
    if payload.asset_damages:
        for asset in payload.asset_damages:
            asset_dict = asset.dict()
            
            # Identify Target Room for this asset
            target_room_number = getattr(asset, 'room_number', checkout_request.room_number)
            room_obj = db.query(Room).filter(Room.number == target_room_number).first()
            if not room_obj or not room_obj.inventory_location_id:
                debug_log(f"[CHECKOUT ERROR] Room {target_room_number} or location not found for asset {asset.item_name}")
                continue

            room_loc_id = room_obj.inventory_location_id
            
            # Asset is charged ONLY if it's actually damaged or if it's missing and NOT being returned
            is_good_moving = getattr(asset, 'is_returned', False) or getattr(asset, 'is_laundry', False)
            should_charge = getattr(asset, 'is_damaged', False) or (not is_good_moving and not getattr(asset, 'is_waste', False))
            
            asset_charge = asset.replacement_cost if should_charge else 0
            if should_charge:
                total_missing_charges += asset_charge
            
            asset_dict['missing_item_charge'] = asset_charge
            asset_dict['unit_price'] = asset.replacement_cost
            asset_dict['missing_qty'] = 1 if should_charge else 0
            asset_dict['is_fixed_asset'] = True
            asset_dict['room_number'] = target_room_number
            
            if should_charge:
                missing_items_details.append({
                    "item_name": asset.item_name,
                    "item_code": "ASSET",
                    "missing_qty": 1,
                    "unit_price": asset.replacement_cost,
                    "total_charge": asset_charge,
                    "is_fixed_asset": True,
                    "notes": asset.notes,
                    "room_number": target_room_number
                })
            
            inventory_data_with_charges.append(asset_dict) 
            
            # Find the Asset Registry Record
            asset_registry_id = getattr(asset, 'asset_registry_id', None)
            item_id = getattr(asset, 'item_id', None)
            
            asset_record = None
            if asset_registry_id:
                asset_record = db.query(AssetRegistry).filter(AssetRegistry.id == asset_registry_id).first()
            elif item_id:
                asset_record = db.query(AssetRegistry).filter(
                    AssetRegistry.item_id == item_id,
                    AssetRegistry.current_location_id == room_loc_id,
                    AssetRegistry.status == "active"
                ).first()
            
            target_item_id = item_id
            target_location_id = room_loc_id
            
            # Determine Return Location for Asset EARLY to avoid scoping errors
            asset_return_loc_id = asset.return_location_id
            if not asset_return_loc_id and asset.is_returned:
                # Fallback to Warehouse
                fallback_loc = db.query(Location).filter(
                    (Location.name.ilike('%warehouse%')) | (Location.location_type == 'WAREHOUSE'),
                    Location.is_active == True,
                    Location.branch_id == branch_id
                ).first()
                if not fallback_loc:
                    fallback_loc = db.query(Location).filter(Location.is_active == True, Location.branch_id == branch_id).first()
                if fallback_loc:
                    asset_return_loc_id = fallback_loc.id
                    print(f"[CHECKOUT-DEBUG] Asset {asset.item_name} using fallback return location {fallback_loc.name}")

            if asset_record:
                if asset.is_damaged:
                    asset_record.status = "damaged"
                    asset_record.notes = f"Damaged during checkout. {asset.notes or ''}"
                elif asset.is_laundry:
                    asset_record.status = "in_laundry"
                elif asset.is_returned:
                    asset_record.status = "active"
                    if asset_return_loc_id:
                        asset_record.current_location_id = asset_return_loc_id
                
                target_item_id = asset_record.item_id
                target_location_id = room_loc_id # Room stock deduction always from room_loc_id
            
            if target_item_id and target_location_id:
                t_item = db.query(InventoryItem).filter(InventoryItem.id == target_item_id).first()
                is_actually_asset = t_item.is_asset_fixed if t_item else True
                
                asset_is_laundry = asset.is_laundry
                asset_laundry_id = asset.laundry_location_id
                
                if not asset_is_laundry and asset.return_location_id:
                    target_loc = db.query(Location).filter(Location.id == asset.return_location_id).first()
                    if target_loc and target_loc.location_type == 'LAUNDRY':
                        asset_is_laundry = True
                        asset_laundry_id = asset.return_location_id

                is_actually_laundry = asset.is_laundry or asset_is_laundry
                if t_item and getattr(t_item, 'track_laundry_cycle', False) and not is_actually_laundry:
                    is_actually_laundry = True
                
                if is_actually_laundry and not asset_laundry_id:
                     first_laundry = db.query(Location).filter(Location.location_type == 'LAUNDRY', Location.is_active == True).first()
                     if first_laundry:
                         asset_laundry_id = first_laundry.id

                should_skip_waste_log = is_actually_laundry or asset.is_returned
                
                if asset.is_damaged and not should_skip_waste_log:
                    if is_actually_asset:
                        waste_log_num = generate_waste_log_number(db, branch_id)
                        waste_log = WasteLog(
                            log_number=waste_log_num,
                            item_id=target_item_id,
                            is_food_item=False,
                            location_id=target_location_id,
                            quantity=1,
                            unit="pcs",
                            reason_code="Damaged",
                            action_taken="Charged to Guest",
                            notes=f"Damaged asset during checkout - Room {target_room_number}. {asset.notes or ''}",
                            reported_by=current_user.id,
                            waste_date=datetime.utcnow(),
                            branch_id=branch_id
                        )
                        db.add(waste_log)
                        db.flush()
                        
                        unit_price = t_item.unit_price or 0 if t_item else 0
                        damage_txn = InventoryTransaction(
                            item_id=target_item_id,
                            transaction_type="waste",
                            quantity=1,
                            unit_price=unit_price,
                            total_amount=asset.replacement_cost,
                            reference_number=waste_log_num,
                            notes=f"WASTE: Damaged asset at checkout - Room {target_room_number}",
                            created_by=current_user.id,
                            source_location_id=target_location_id,
                            branch_id=branch_id
                        )
                        db.add(damage_txn)
                    else:
                        damage_txn = InventoryTransaction(
                            item_id=target_item_id,
                            transaction_type="waste",
                            quantity=1,
                            unit_price=t_item.unit_price if t_item else 0,
                            total_amount=asset.replacement_cost,
                            reference_number=f"LOST-DAM-{checkout_request.id}",
                            notes=f"WASTE: Damaged item at checkout - Room {target_room_number}",
                            created_by=current_user.id,
                            source_location_id=target_location_id,
                            branch_id=branch_id
                        )
                        db.add(damage_txn)
                
                # Deduct LocationStock
                if is_actually_laundry or asset.is_returned or asset.is_waste or asset.is_damaged:
                    loc_stock = db.query(LocationStock).filter(
                        LocationStock.location_id == target_location_id,
                        LocationStock.item_id == target_item_id
                    ).first()
                    if loc_stock:
                        loc_stock.quantity = max(0, loc_stock.quantity - 1)
                        loc_stock.last_updated = datetime.utcnow()

                # Deactivate Asset Mapping SURGICALLY
                # We decrement quantity or deactivate if count hits zero
                mapping_to_update = db.query(AssetMapping).filter(
                   AssetMapping.location_id == target_location_id,
                   AssetMapping.item_id == target_item_id,
                   AssetMapping.is_active == True
                ).first()
                
                if mapping_to_update:
                    if mapping_to_update.quantity > 1:
                        mapping_to_update.quantity -= 1
                        db.add(mapping_to_update)
                    else:
                        mapping_to_update.is_active = False
                        db.add(mapping_to_update)

                # Deduct Global Stock (Only if MISSING or WASTE)
                inv_item_obj = db.query(InventoryItem).filter(InventoryItem.id == target_item_id).first()
                if inv_item_obj:
                    should_deduct_global = should_charge and not (asset_is_laundry or asset.is_returned or asset.is_waste)
                    if asset.is_waste: should_deduct_global = True
                    if should_deduct_global:
                        inv_item_obj.current_stock -= 1

                # Laundry/Waste movement
                if is_actually_laundry and asset_laundry_id:
                    if asset_record:
                        asset_record.current_location_id = asset_laundry_id
                        asset_record.status = "in_laundry"
                    
                    l_stock = db.query(LocationStock).filter(
                        LocationStock.location_id == asset_laundry_id,
                        LocationStock.item_id == target_item_id
                    ).first()
                    if l_stock:
                        l_stock.quantity += 1
                    else:
                        db.add(LocationStock(location_id=asset_laundry_id, item_id=target_item_id, quantity=1, last_updated=datetime.utcnow(), branch_id=branch_id))
                    
                    laundry_entry = LaundryLog(
                        item_id=target_item_id,
                        source_location_id=target_location_id,
                        room_number=target_room_number,
                        quantity=1,
                        status="Incomplete Washing",
                        sent_at=datetime.utcnow(),
                        created_by=current_user.id,
                        notes=f"Asset movement at checkout - Room {target_room_number}",
                        branch_id=branch_id
                    )
                    db.add(laundry_entry)

                    laundry_txn = InventoryTransaction(
                        item_id=target_item_id,
                        transaction_type="transfer",
                        quantity=1,
                        unit_price=0.0,
                        reference_number=f"LAUNDRY-CHK-{checkout_request.id}",
                        notes=f"Linen to Laundry - Room {target_room_number}",
                        created_by=current_user.id,
                        source_location_id=target_location_id,
                        destination_location_id=asset_laundry_id,
                        branch_id=branch_id
                    )
                    db.add(laundry_txn)

                # Asset Return movement to destination stock
                elif asset.is_returned and asset_return_loc_id:
                    dest_stock = db.query(LocationStock).filter(
                        LocationStock.location_id == asset_return_loc_id,
                        LocationStock.item_id == target_item_id
                    ).first()
                    if dest_stock:
                        dest_stock.quantity += 1
                    else:
                        db.add(LocationStock(location_id=asset_return_loc_id, item_id=target_item_id, quantity=1, last_updated=datetime.utcnow(), branch_id=branch_id))
                    
                    return_txn = InventoryTransaction(
                        item_id=target_item_id,
                        transaction_type="transfer_in",
                        quantity=1,
                        unit_price=t_item.unit_price if t_item else 0.0,
                        reference_number=f"RET-CHK-{checkout_request.id}",
                        notes=f"Asset Return - Room {target_room_number}",
                        created_by=current_user.id,
                        source_location_id=room_loc_id,
                        destination_location_id=asset_return_loc_id,
                        branch_id=branch_id
                    )
                    db.add(return_txn)
                    
                    # Update global stock if returning to warehouse
                    return_loc = db.query(Location).filter(Location.id == asset_return_loc_id).first()
                    if return_loc and return_loc.location_type:
                        if return_loc.location_type.upper() in ["WAREHOUSE", "CENTRAL_WAREHOUSE", "BRANCH_STORE"]:
                             if t_item:
                                 t_item.current_stock = (t_item.current_stock or 0) + 1

                    if asset.request_replacement:
                         default_store = db.query(Location).filter(Location.location_type == 'WAREHOUSE', Location.is_active == True).first()
                         new_sr = ServiceRequest(
                            room_id=room_obj.id,
                            request_type="replenishment",
                            description=f"REPLACEMENT REQUIRED: {t_item.name if t_item else asset.item_name} (Fixed Asset) sent to laundry. Fresh unit needed for Room {target_room_number}." if is_actually_asset else f"LINEN/LAUNDRY REFILL: {t_item.name if t_item else asset.item_name} for Room {target_room_number}.",
                            status="pending",
                            pickup_location_id=default_store.id if default_store else None,
                            created_at=datetime.utcnow(),
                            branch_id=branch_id,
                            refill_data=json.dumps([{
                                "item_id": target_item_id,
                                "quantity": 1,
                                "item_name": t_item.name if t_item else asset.item_name,
                                "unit": t_item.unit if t_item else "pcs",
                                "is_fixed_asset": is_actually_asset,
                                "source_location_id": target_location_id
                            }])
                        )
                         db.add(new_sr)
                
                elif asset.is_waste and asset.waste_location_id:
                    if asset_record:
                        asset_record.current_location_id = asset.waste_location_id
                        asset_record.status = "waste"
                    waste_stock = db.query(LocationStock).filter(
                        LocationStock.location_id == asset.waste_location_id,
                        LocationStock.item_id == target_item_id
                    ).first()
                    if waste_stock:
                        waste_stock.quantity += 1
                    else:
                        db.add(LocationStock(location_id=asset.waste_location_id, item_id=target_item_id, quantity=1, last_updated=datetime.utcnow(), branch_id=branch_id))

                elif asset.is_returned and asset.return_location_id:
                    if asset_record:
                        asset_record.current_location_id = asset.return_location_id
                        asset_record.status = "active"
                    return_stock = db.query(LocationStock).filter(
                        LocationStock.location_id == asset.return_location_id,
                        LocationStock.item_id == target_item_id
                    ).first()
                    if return_stock:
                        return_stock.quantity += 1
                    else:
                        db.add(LocationStock(location_id=asset.return_location_id, item_id=target_item_id, quantity=1, last_updated=datetime.utcnow(), branch_id=branch_id))
                    
                    # ADDED: Transaction for returned asset
                    asset_return_txn = InventoryTransaction(
                        item_id=target_item_id,
                        transaction_type="transfer_in", # Corrected for history visibility
                        quantity=1,
                        unit_price=t_item.unit_price if t_item else 0.0,
                        total_amount=0.0,
                        reference_number=f"ASSET-RET-{checkout_request.id}",
                        notes=f"Asset returned at checkout - Room {target_room_number}",
                        created_by=current_user.id,
                        source_location_id=target_location_id,
                        destination_location_id=asset.return_location_id,
                        branch_id=branch_id
                    )
                    db.add(asset_return_txn)
                    
                    # ADDED: Update global current_stock for returned assets
                    return_loc_asset = db.query(Location).filter(Location.id == asset.return_location_id).first()
                    if return_loc_asset and return_loc_asset.location_type:
                        if return_loc_asset.location_type.upper() in ["WAREHOUSE", "CENTRAL_WAREHOUSE", "BRANCH_STORE", "REPAIR", "LAUNDRY"]:
                            if inv_item_obj:
                                inv_item_obj.current_stock = (inv_item_obj.current_stock or 0) + 1
                                print(f"[CHECKOUT-DEBUG] Fixed Asset {t_item.name if t_item else 'Unknown'} returned to global stock (+1)")

                elif asset.request_replacement:
                    default_store = db.query(Location).filter(Location.location_type == 'WAREHOUSE', Location.is_active == True).first()
                    new_sr = ServiceRequest(
                        room_id=room_obj.id,
                        request_type="replenishment",
                        description=f"REPLACEMENT REQUIRED: {t_item.name if t_item else asset.item_name} (Fixed Asset) requested for Room {target_room_number} during checkout." if is_actually_asset else f"LINEN/LAUNDRY REFILL: {t_item.name if t_item else asset.item_name} for Room {target_room_number}.",
                        status="pending",
                        pickup_location_id=default_store.id if default_store else None,
                        created_at=datetime.utcnow(),
                        branch_id=branch_id,
                        refill_data=json.dumps([{
                            "item_id": target_item_id,
                            "quantity": 1,
                            "item_name": t_item.name if t_item else asset.item_name,
                            "unit": t_item.unit if t_item else "pcs",
                            "is_fixed_asset": is_actually_asset,
                            "source_location_id": target_location_id
                        }])
                    )
                    db.add(new_sr)

    if inventory_data_with_charges:
        checkout_request.inventory_data = inventory_data_with_charges
    else:
        # Ensure inventory_data is at least an empty list, not None
        checkout_request.inventory_data = []
        
    checkout_request.status = "completed"
    checkout_request.completed_at = datetime.utcnow()
    
    # NEW: Consolidate workflow - Complete any existing 'return_items' service requests for this room
    try:
        # Determine room ID if not already available
        if not room_obj:
            room_obj = db.query(Room).filter(Room.number == checkout_request.room_number).first()
        
        if room_obj:
            pending_returns = db.query(ServiceRequest).filter(
                ServiceRequest.room_id == room_obj.id,
                ServiceRequest.request_type == "return_items",
                ServiceRequest.status.notin_(["completed", "cancelled"])
            ).all()
            
            for return_req in pending_returns:
                return_req.status = "completed"
                return_req.completed_at = datetime.utcnow()
                return_req.description += f" | Auto-completed via Checkout Verification #{checkout_request.id}"
                print(f"[CHECKOUT] Auto-completed redundant 'return_items' service request #{return_req.id} for Room {room_obj.number}")
    except Exception as cleanup_error:
        print(f"[WARNING] Failed to cleanup redundant service requests: {cleanup_error}")

    db.commit()
    db.refresh(checkout_request)
    
    return {
        "message": "Inventory checked and checkout request completed successfully",
        "request_id": checkout_request.id,
        "status": checkout_request.status,
        "inventory_checked": True,
        "missing_items_charge": total_missing_charges,
        "missing_items_details": missing_items_details
    }


@router.get("/pre-checkout/{room_number}/verification-data")
def get_pre_checkout_verification_data(room_number: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user), branch_id: int = Depends(get_branch_id)):
    """
    Get pre-checkout verification data for a room:
    - Room status
    - Actual Consumables stock in room (from LocationStock)
    - Actual Fixed Assets in room (from AssetRegistry) with serial numbers
    """
    room = db.query(Room).filter(Room.number == room_number, Room.branch_id == branch_id).first()
    if not room:
        raise HTTPException(status_code=404, detail=f"Room {room_number} not found")
    
    # Get booking info
    booking_link = (db.query(BookingRoom)
                    .join(Booking)
                    .filter(BookingRoom.room_id == room.id, Booking.status.in_(['checked-in', 'checked_in', 'booked']))
                    .order_by(Booking.id.desc()).first())
    
    package_link = None
    booking = None
    if booking_link:
        booking = booking_link.booking
    else:
        package_link = (db.query(PackageBookingRoom)
                        .join(PackageBooking)
                        .filter(PackageBookingRoom.room_id == room.id, PackageBooking.status.in_(['checked-in', 'checked_in', 'booked']))
                        .order_by(PackageBooking.id.desc()).first())
        if package_link:
            booking = package_link.package_booking
    
    if not booking:
        # Allow checking inventory even if booking is weird, but warn?
        # raise HTTPException(status_code=404, detail=f"No active booking found for room {room_number}")
        pass
    
    consumables = []
    assets = []
    
    # Check if room has an inventory location assigned
    if room.inventory_location_id:
        # Models already imported at top of file
        from app.models.inventory import InventoryCategory
        
        # 1. Fetch Consumables (LocationStock)
        # We assume anything in LocationStock that is consumable/sellable is a consumable
        loc_stocks = db.query(LocationStock).join(InventoryItem).join(InventoryCategory).filter(
            LocationStock.location_id == room.inventory_location_id,
            InventoryCategory.classification != "Asset" # Exclude assets if mixed, though normally separated
        ).all()
        
        # Filter for consumables/amenities specifically? Or just show all stock? User said "all invetry items"
        # Aggregation Dictionary to merge duplicate Consumables/Rentals
        # Key: (item_id, is_rent_flag, is_fixed_flag) -> Data Object
        aggregated_consumables = {}
        
        for stock in loc_stocks:
             if stock.quantity > 0 or stock.item.category.consumable_instant:
                # Stock details logic
                from app.models.inventory import StockIssue, StockIssueDetail
                
                issue_details = db.query(StockIssueDetail).join(StockIssue).filter(
                    StockIssueDetail.item_id == stock.item_id,
                    StockIssue.destination_location_id == room.inventory_location_id
                ).all()
                
                is_fixed_asset_flag = (
                    (stock.item.category.classification and stock.item.category.classification.lower() in ["asset", "fixed asset"]) or 
                    stock.item.is_asset_fixed or 
                    stock.item.category.is_asset_fixed
                )

                # Split logic
                # CHANGE: Only consider items with an actual rental price as 'rented'
                # is_payable means the guest pays for consumption, not necessarily a 'rental'
                rented_details = [d for d in issue_details if (d.rental_price and d.rental_price > 0)]
                non_rented_details = [d for d in issue_details if not (d.rental_price and d.rental_price > 0)]
                
                rented_qty_total = sum(d.issued_quantity for d in rented_details)
                rented_qty_total = min(stock.quantity, rented_qty_total)
                
                standard_qty_total = max(0, stock.quantity - rented_qty_total)

                def update_aggregate(qty, details, is_rent, is_fixed):
                    # FIX: Group by Item and Fixed Status only. 
                    # Do NOT group by 'is_rent'. This allows Payable (Rent=True) and Complimentary (Rent=False) 
                    # consumables to be merged into a single row.
                    key = (stock.item_id, is_fixed)
                    
                    if key not in aggregated_consumables:
                        aggregated_consumables[key] = {
                            "item_id": stock.item_id,
                            "item_name": stock.item.name,
                            "current_stock": 0.0,
                            "complimentary_qty": 0.0,
                            "payable_qty": 0.0,
                            "payable_price": 0.0,
                            "complimentary_limit": stock.item.complimentary_limit or 0,
                            "unit": stock.item.unit,
                            "cost_per_unit": stock.item.unit_price or 0.0,
                            "is_fixed_asset": is_fixed,
                            "is_rentable": False, # Initialize as False, OR-accumulate below
                            "track_laundry_cycle": stock.item.track_laundry_cycle
                        }
                    
                    agg = aggregated_consumables[key]
                    agg["current_stock"] += qty
                    agg["is_rentable"] = agg["is_rentable"] or is_rent
                    
                    for detail in details:
                         if detail.is_payable:
                             agg["payable_qty"] += detail.issued_quantity
                             p_price = detail.rental_price if detail.rental_price and detail.rental_price > 0 else (detail.unit_price)
                             if p_price and p_price > 0:
                                 agg["payable_price"] = float(p_price)
                         else:
                             agg["complimentary_qty"] += detail.issued_quantity
                
                if rented_qty_total > 0:
                    update_aggregate(rented_qty_total, rented_details, is_rent=True, is_fixed=False)
                    
                if standard_qty_total > 0 or (stock.item.category.consumable_instant and rented_qty_total == 0):
                    update_aggregate(standard_qty_total, non_rented_details, is_rent=False, is_fixed=is_fixed_asset_flag)

        # Convert Aggregated Data to Final List
        for key, data in aggregated_consumables.items():
             selling_price = data["payable_price"] if data["payable_price"] > 0 else 0.0
             
             # Fallback selling price if not found in transaction details
             if selling_price == 0.0:
                  pass

             # Re-fetch item selling price if needed? 
             if selling_price == 0.0:
                  stock_item = db.query(InventoryItem).filter(InventoryItem.id == data["item_id"]).first()
                  if stock_item:
                      selling_price = stock_item.selling_price or stock_item.unit_price or 0.0

             potential_charge = data["payable_qty"] * selling_price
             
             consumables.append({
                 "item_id": data["item_id"],
                 "item_name": data["item_name"],
                 "current_stock": data["current_stock"],
                 "complimentary_qty": data["complimentary_qty"],
                 "payable_qty": data["payable_qty"],
                 "complimentary_limit": data["complimentary_limit"],
                 "charge_per_unit": selling_price,
                 "cost_per_unit": data["cost_per_unit"],
                 "potential_charge": potential_charge,
                 "unit": data["unit"],
                 "is_fixed_asset": data["is_fixed_asset"],
                 "is_payable": (data["payable_qty"] > 0),
                 "is_rentable": data["is_rentable"],
                 "track_laundry_cycle": data["track_laundry_cycle"],
             })

        # 2. Fetch Fixed Assets (AssetRegistry)
        # These are individual items with serial numbers
        room_assets = db.query(AssetRegistry).join(InventoryItem).filter(
            AssetRegistry.current_location_id == room.inventory_location_id,
            AssetRegistry.status == "active"
        ).all()
        
        for asset in room_assets:
            assets.append({
                "asset_registry_id": asset.id,
                "item_id": asset.item_id,
                "item_name": asset.item.name,
                "replacement_cost": asset.item.selling_price or asset.item.unit_price or 0.0,
                "serial_number": asset.serial_number,
                "asset_tag": asset.asset_tag_id,
                "current_stock": 1, # It's a single unit
                "track_laundry_cycle": asset.item.track_laundry_cycle,
                "is_rentable": asset.item.is_asset_fixed == False # Or some logic to determine if it's a rental asset
            })
            
    # Fallback if no location assigned or empty: return general lists as before (or empty)?
    # User specifically asked for "in the room with any serial number". 
    # If no location ID, we can't really know what's IN the room accurately.
    # We will just return empty lists if no location_id, prompting setup.
    
    # Validation/Fallback query for assets if AssetRegistry is empty but using old system?
    # Skipping legacy support for now to encourage correct usage, unless requested.

    # Default key card fee
    key_card_fee = 50.0
    
    return {
        "room_number": room_number,
        "inventory_location_id": room.inventory_location_id,
        "room_status": room.status,
        "housekeeping_status": "pending",
        "consumables": consumables,
        "assets": assets,
        "key_card_fee": key_card_fee,
        "booking_info": {
            "guest_name": booking.guest_name if booking else "N/A",
            "check_in": str(booking.check_in) if booking else None,
            "check_out": str(booking.check_out) if booking else None,
            "advance_deposit": getattr(booking, 'advance_deposit', 0.0) or 0.0 if booking else 0.0
        }
    }


@router.get("/checkout/{checkout_id}/invoice")
def generate_invoice(checkout_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Generate tax invoice PDF for a checkout
    Includes HSN codes, tax breakdown, QR code, and GSTIN if B2B
    """
    checkout = db.query(Checkout).filter(Checkout.id == checkout_id).first()
    if not checkout:
        raise HTTPException(status_code=404, detail="Checkout not found")
    
    # Get booking details
    booking = None
    if checkout.booking_id:
        booking = db.query(Booking).filter(Booking.id == checkout.booking_id).first()
    elif checkout.package_booking_id:
        booking = db.query(PackageBooking).filter(PackageBooking.id == checkout.package_booking_id).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found for this checkout")
    
    # Get verification data
    verifications = db.query(CheckoutVerification).filter(CheckoutVerification.checkout_id == checkout_id).all()
    
    # Get payment details
    payments = db.query(CheckoutPayment).filter(CheckoutPayment.checkout_id == checkout_id).all()
    
    # Build invoice data
    invoice_data = {
        "invoice_number": checkout.invoice_number or f"INV-{checkout_id}",
        "invoice_date": checkout.checkout_date.strftime("%d-%m-%Y") if checkout.checkout_date else datetime.now().strftime("%d-%m-%Y"),
        "guest_name": checkout.guest_name,
        "guest_mobile": booking.guest_mobile if booking else None,
        "guest_email": booking.guest_email if booking else None,
        "guest_gstin": checkout.guest_gstin,
        "is_b2b": checkout.is_b2b,
        "room_number": checkout.room_number,
        "check_in": str(booking.check_in) if booking else None,
        "check_out": str(booking.check_out) if booking else None,
        "charges": {
            "room_total": checkout.room_total,
            "food_total": checkout.food_total,
            "service_total": checkout.service_total,
            "package_total": checkout.package_total,
            "consumables_charges": checkout.consumables_charges,
            "asset_damage_charges": checkout.asset_damage_charges,
            "key_card_fee": checkout.key_card_fee,
            "late_checkout_fee": checkout.late_checkout_fee,
            "subtotal": checkout.room_total + checkout.food_total + checkout.service_total + 
                       checkout.package_total + checkout.consumables_charges + 
                       checkout.asset_damage_charges + checkout.key_card_fee + checkout.late_checkout_fee,
            "tax_amount": checkout.tax_amount,
            "discount_amount": checkout.discount_amount,
            "advance_deposit": checkout.advance_deposit,
            "tips_gratuity": checkout.tips_gratuity,
            "grand_total": checkout.grand_total
        },
        "verifications": [
            {
                "room_number": v.room_number,
                "housekeeping_status": v.housekeeping_status,
                "consumables_total": v.consumables_total_charge,
                "asset_damage_total": v.asset_damage_total,
                "key_card_fee": v.key_card_fee
            }
            for v in verifications
        ],
        "payments": [
            {
                "method": p.payment_method,
                "amount": p.amount,
                "transaction_id": p.transaction_id
            }
            for p in payments
        ]
    }
    
    # TODO: Generate actual PDF using reportlab or similar
    # For now, return JSON data that frontend can use to generate PDF
    return invoice_data


@router.get("/checkout/{checkout_id}/gate-pass")
def generate_gate_pass(checkout_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Generate gate pass for security (proof of payment for vehicle exit)
    """
    checkout = db.query(Checkout).filter(Checkout.id == checkout_id).first()
    if not checkout:
        raise HTTPException(status_code=404, detail="Checkout not found")
    
    gate_pass_data = {
        "gate_pass_number": f"GP-{checkout_id}-{datetime.now().strftime('%Y%m%d')}",
        "checkout_id": checkout_id,
        "guest_name": checkout.guest_name,
        "room_number": checkout.room_number,
        "checkout_date": checkout.checkout_date.strftime("%d-%m-%Y %H:%M") if checkout.checkout_date else None,
        "payment_status": checkout.payment_status,
        "grand_total": checkout.grand_total,
        "generated_at": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    }
    
    # TODO: Generate actual gate pass PDF/slip
    return gate_pass_data


@router.post("/checkout/{checkout_id}/send-feedback")
def send_feedback_form(checkout_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Trigger guest feedback form email/SMS
    """
    checkout = db.query(Checkout).filter(Checkout.id == checkout_id).first()
    if not checkout:
        raise HTTPException(status_code=404, detail="Checkout not found")
    
    booking = None
    if checkout.booking_id:
        booking = db.query(Booking).filter(Booking.id == checkout.booking_id).first()
    elif checkout.package_booking_id:
        booking = db.query(PackageBooking).filter(PackageBooking.id == checkout.package_booking_id).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Mark feedback as sent
    checkout.feedback_sent = True
    db.commit()
    
    # TODO: Send actual email/SMS with feedback link
    # For now, return feedback link
    feedback_link = f"https://your-resort.com/feedback/{checkout_id}"
    
    return {
        "message": "Feedback form sent successfully",
        "feedback_link": feedback_link,
        "guest_email": booking.guest_email,
        "guest_mobile": booking.guest_mobile
    }


from app.utils.branch_scope import get_branch_id

@router.get("/checkouts", response_model=List[CheckoutFull])
def get_all_checkouts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), skip: int = 0, limit: int = 20, branch_id: int = Depends(get_branch_id)):
    """Retrieves a list of all completed checkouts, ordered by most recent - optimized for low network"""
    from app.utils.api_optimization import optimize_limit, MAX_LIMIT_LOW_NETWORK
    limit = optimize_limit(limit, MAX_LIMIT_LOW_NETWORK)
    
    query = db.query(Checkout)
    if branch_id is not None:
        query = query.filter(Checkout.branch_id == branch_id)
        
    checkouts = query.order_by(Checkout.id.desc()).offset(skip).limit(limit).all()
    print(f"DEBUG: get_all_checkouts - Found {len(checkouts)} checkouts")
    return checkouts if checkouts else []

@router.post("/cleanup-orphaned-checkouts")
def cleanup_orphaned_checkouts_endpoint(
    room_number: Optional[str] = Query(None),
    booking_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):
    """
    Manual cleanup endpoint for orphaned checkouts.
    Can clean up by room_number or booking_id.
    """
    try:
        deleted_count = 0
        checkouts_to_delete = []
        
        if room_number:
            # Find checkouts for this room where room is still checked-in
            room = db.query(Room).filter(Room.number == room_number, Room.branch_id == branch_id).first()
            if not room:
                raise HTTPException(status_code=404, detail=f"Room {room_number} not found")
            
            if room.status != "Available":
                checkouts = db.query(Checkout).filter(
                    Checkout.room_number == room_number
                ).all()
                checkouts_to_delete.extend(checkouts)
        
        if booking_id:
            # Find checkouts for this booking
            booking = db.query(Booking).filter(Booking.id == booking_id).first()
            if not booking:
                raise HTTPException(status_code=404, detail=f"Booking {booking_id} not found")
            
            checkouts = db.query(Checkout).filter(
                Checkout.booking_id == booking_id
            ).all()
            checkouts_to_delete.extend(checkouts)
        
        # Remove duplicates
        unique_checkouts = {c.id: c for c in checkouts_to_delete}.values()
        
        for checkout in unique_checkouts:
            room = db.query(Room).filter(Room.number == checkout.room_number).first()
            if room and room.status != "Available":
                db.delete(checkout)
                deleted_count += 1
                print(f"[CLEANUP] Deleted orphaned checkout {checkout.id} for room {checkout.room_number}")
        
        db.commit()
        
        return {
            "message": f"Cleaned up {deleted_count} orphaned checkout(s)",
            "deleted_count": deleted_count
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

@router.post("/repair-room-status/{room_number}")
def repair_room_checkout_status(room_number: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user), branch_id: int = Depends(get_branch_id)):
    """
    Repair function to fix mismatched checkout status.
    If a checkout record exists but room is not marked as Available, fix the room status.
    If room is Available but no checkout record exists, create a minimal checkout record.
    """
    room = db.query(Room).filter(Room.number == room_number, Room.branch_id == branch_id).first()
    if not room:
        raise HTTPException(status_code=404, detail=f"Room {room_number} not found")
        
    today = date.today()
    existing_checkout = db.query(Checkout).filter(
        Checkout.room_number == room_number,
        func.date(Checkout.checkout_date) == today
    ).first()
    
    # Find the booking
    booking_link = (db.query(BookingRoom)
                    .join(Booking)
                    .filter(BookingRoom.room_id == room.id)
                    .order_by(Booking.id.desc()).first())
    
    package_link = None
    booking = None
    is_package = False
    
    if booking_link:
        booking = booking_link.booking
    else:
        package_link = (db.query(PackageBookingRoom)
                       .join(PackageBooking)
                       .filter(PackageBookingRoom.room_id == room.id)
                       .order_by(PackageBooking.id.desc()).first())
        if package_link:
            booking = package_link.package_booking
            is_package = True
    
    repairs_made = []
    
    # Case 1: Checkout record exists but room is not Available
    if existing_checkout and room.status != "Available":
        room.status = "Available"
        repairs_made.append(f"Updated room {room_number} status to 'Available' (checkout record exists)")
        
        # Check if all rooms in booking are checked out
        if booking:
            if is_package:
                remaining_rooms = [link.room for link in booking.rooms if link.room.status != "Available"]
            else:
                remaining_rooms = [link.room for link in booking.booking_rooms if link.room.status != "Available"]
            
            if not remaining_rooms and booking.status not in ['checked_out', 'checked-out']:
                booking.status = "checked_out"
                booking.checked_out_at = datetime.utcnow()
                repairs_made.append(f"Updated booking {booking.id} status to 'checked_out' (all rooms checked out)")
    
    # Case 2: Room is Available but no checkout record (might have been manually set)
    elif room.status == "Available" and not existing_checkout:
        # Room is available but no checkout record - this is okay, just note it
        repairs_made.append(f"Room {room_number} is Available but no checkout record found (this is okay if room was manually set)")
    
    # Case 3: Booking status is checked_out but room is not Available
    elif booking and booking.status in ['checked_out', 'checked-out'] and room.status != "Available":
        # This shouldn't happen, but fix it
        if existing_checkout:
            room.status = "Available"

            
            # 13.1. Return remaining consumables to warehouse
            try:
                if room.inventory_location_id:
                    from app.models.inventory import LocationStock, Location, InventoryTransaction, InventoryItem
                    from sqlalchemy.orm import joinedload
                    
                    remaining = db.query(LocationStock).join(InventoryItem).options(
                        joinedload(LocationStock.item)
                    ).filter(
                        LocationStock.location_id == room.inventory_location_id,
                        LocationStock.quantity > 0,
                        InventoryItem.is_asset_fixed == False
                    ).all()
                    
                    if remaining:
                        warehouse = db.query(Location).filter(Location.location_type == "WAREHOUSE").first()
                        laundry = db.query(Location).filter(
                            (Location.location_type == "LAUNDRY") | 
                            (Location.name.ilike("%Laundry%"))
                        ).first()

                        if warehouse:
                            for item_stock in remaining:
                                qty = item_stock.quantity
                                item_name = item_stock.item.name if item_stock.item else f"Item #{item_stock.item_id}"
                                
                                # Determine destination: Laundry or Warehouse
                                target_location = warehouse
                                if item_stock.item.track_laundry_cycle and laundry:
                                    target_location = laundry
                                    print(f"[CLEANUP] Item {item_name} is marked for Laundry. Redirecting to {laundry.name}")

                                # Proceed with transfer to target_location
                                dest_stock = db.query(LocationStock).filter(
                                    LocationStock.location_id == target_location.id,
                                    LocationStock.item_id == item_stock.item_id
                                ).first()
                                
                                if dest_stock:
                                    dest_stock.quantity += qty
                                    dest_stock.last_updated = datetime.utcnow()
                                else:
                                    db.add(LocationStock(
                                        location_id=target_location.id,
                                        item_id=item_stock.item_id,
                                        quantity=qty,
                                        last_updated=datetime.utcnow(),
                                        branch_id=branch_id
                                    ))
                                
                                db.add(InventoryTransaction(
                                    item_id=item_stock.item_id,
                                    transaction_type="transfer_out",
                                    quantity=-qty,
                                    notes=f"Checkout cleanup - returned from Room {room.number} to {target_location.name}",
                                    created_by=current_user.id if current_user else None,
                                    source_location_id=room.inventory_location_id,
                                    destination_location_id=target_location.id,
                                    branch_id=branch_id
                                ))
                                
                                item_stock.quantity = 0
                                item_stock.last_updated = datetime.utcnow()
                                print(f"[CLEANUP] Returned {qty} x {item_name} from Room {room.number}")
            except Exception as e:
                print(f"[WARNING] Cleanup failed: {e}")
            repairs_made.append(f"Fixed room {room_number} status to match booking status")
        else:
            # Booking says checked out but room and checkout don't match - reset booking status
            booking.status = "checked-in"
            repairs_made.append(f"Reset booking {booking.id} status to 'checked-in' (room not actually checked out)")
    
    if repairs_made:
        db.commit()
        return {"message": "Repairs completed", "repairs": repairs_made}
    else:
        return {"message": "No repairs needed", "status": "Room and booking status are consistent"}

@router.get("/checkouts/{checkout_id}/details")
def get_checkout_details(checkout_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get detailed checkout information including food orders and services."""
    checkout = db.query(Checkout).filter(Checkout.id == checkout_id).first()
    if not checkout:
        raise HTTPException(status_code=404, detail="Checkout not found")
    
    # Get room numbers using a set to avoid duplicates
    room_numbers_set = set()
    if checkout.room_number:
        room_numbers_set.add(checkout.room_number)
        
    booking_details = None
    check_in = None
    
    if checkout.booking_id:
        booking = db.query(Booking).options(
            joinedload(Booking.booking_rooms).joinedload(BookingRoom.room)
        ).filter(Booking.id == checkout.booking_id).first()
        if booking:
            for br in booking.booking_rooms:
                if br.room:
                    room_numbers_set.add(br.room.number)
            
            check_in = booking.check_in
            booking_details = {
                "check_in": str(booking.check_in),
                "check_out": str(booking.check_out),
                "adults": booking.adults,
                "children": booking.children,
                "status": booking.status
            }
    elif checkout.package_booking_id:
        package_booking = db.query(PackageBooking).options(
            joinedload(PackageBooking.rooms).joinedload(PackageBookingRoom.room)
        ).filter(PackageBooking.id == checkout.package_booking_id).first()
        if package_booking:
            for pbr in package_booking.rooms:
                if pbr.room:
                    room_numbers_set.add(pbr.room.number)
            
            check_in = package_booking.check_in
            booking_details = {
                "check_in": str(package_booking.check_in),
                "check_out": str(package_booking.check_out),
                "adults": package_booking.adults,
                "children": package_booking.children,
                "status": package_booking.status,
                "package_name": package_booking.package.title if package_booking.package else None
            }
            
    room_numbers = list(room_numbers_set)
    
    # Get food orders for these rooms
    food_orders = []
    if room_numbers:
        rooms = db.query(Room).filter(Room.number.in_(room_numbers)).all()
        room_ids = [r.id for r in rooms]
        if room_ids:
            fo_query = db.query(FoodOrder).options(
                joinedload(FoodOrder.items).joinedload(FoodOrderItem.food_item)
            ).filter(FoodOrder.room_id.in_(room_ids))
            
            if check_in:
                fo_query = fo_query.filter(FoodOrder.created_at >= check_in)
                
            orders = fo_query.all()
            for order in orders:
                food_orders.append({
                    "id": order.id,
                    "room_number": next((r.number for r in rooms if r.id == order.room_id), None),
                    "amount": order.amount,
                    "status": order.status,
                    "created_at": order.created_at.isoformat() if order.created_at else None,
                    "items": [
                        {
                            "item_name": item.food_item.name if item.food_item else "Unknown",
                            "quantity": item.quantity,
                            "price": item.food_item.price if item.food_item else 0,
                            "total": item.quantity * (item.food_item.price if item.food_item else 0)
                        }
                        for item in order.items
                    ]
                })
    
    # Get services for these rooms
    services = []
    if room_numbers:
        rooms = db.query(Room).filter(Room.number.in_(room_numbers)).all()
        room_ids = [r.id for r in rooms]
        if room_ids:
            svc_query = db.query(AssignedService).options(
                joinedload(AssignedService.service)
            ).filter(AssignedService.room_id.in_(room_ids))
            
            if check_in:
                svc_query = svc_query.filter(AssignedService.assigned_at >= check_in)
                
            assigned_services = svc_query.all()
            for ass in assigned_services:
                services.append({
                    "id": ass.id,
                    "room_number": next((r.number for r in rooms if r.id == ass.room_id), None),
                    "service_name": ass.service.name if ass.service else "Unknown",
                    "charges": ass.service.charges if ass.service else 0,
                    "status": ass.status,
                    "created_at": ass.assigned_at.isoformat() if ass.assigned_at else None
                })
    
    # Reconstruct bill_details if missing
    bill_details = checkout.bill_details
    if not bill_details:
        checkout_req = db.query(CheckoutRequestModel).filter(
            CheckoutRequestModel.checkout_id == checkout.id
        ).first()
        
        # Or try matching by booking_id/room if checkout_id not linked
        if not checkout_req and checkout.booking_id:
            checkout_req = db.query(CheckoutRequestModel).filter(
                CheckoutRequestModel.booking_id == checkout.booking_id,
                CheckoutRequestModel.status == "completed"
            ).order_by(CheckoutRequestModel.id.desc()).first()
            
        if checkout_req and checkout_req.inventory_data:
            consumables_items = []
            asset_damages = []
            inv_charges = 0.0
            cons_charges = 0.0
            damage_charges = 0.0
            
            for item in checkout_req.inventory_data:
                # Assuming item format from handleCompleteCheckoutRequest
                t_charge = float(item.get('total_charge', 0) or 0)
                missing_charge = float(item.get('missing_item_charge', 0) or 0)
                damage_charge = float(item.get('damage_charge', 0) or 0)
                
                charge = t_charge + missing_charge + damage_charge
                
                is_asset = item.get('is_fixed_asset', False)
                is_damaged = (item.get('damage_qty', 0) > 0 or item.get('missing_qty', 0) > 0)
                
                if charge > 0:
                    if is_damaged and is_asset:
                        asset_damages.append({
                            "item_name": item.get('item_name'),
                            "total_charge": charge,
                            "notes": item.get('notes', 'Damaged/Missing')
                        })
                        damage_charges += charge
                    else:
                        consumables_items.append({
                            "item_name": item.get('item_name'),
                            "quantity": item.get('payable_usage_qty', 0) or (item.get('missing_qty', 0) + item.get('damage_qty', 0)),
                            "total_charge": charge,
                            "charge_per_unit": item.get('unit_price', 0),
                            "complimentary_limit": item.get('complimentary_limit', 0)
                        })
                        if item.get('is_rentable', False):
                            inv_charges += charge
                        else:
                            cons_charges += charge
            
            bill_details = {
                "consumables_items": consumables_items,
                "asset_damages": asset_damages,
                "consumables_charges": cons_charges,
                "inventory_charges": inv_charges,
                "asset_damage_charges": damage_charges
            }
            
    # Self-healing totals
    final_food_total = checkout.food_total
    if final_food_total == 0 and food_orders:
         final_food_total = sum(o['amount'] for o in food_orders)
         
    final_service_total = checkout.service_total
    if final_service_total == 0 and services:
         final_service_total = sum(s['charges'] for s in services)

    final_consumables_charges = checkout.consumables_charges
    final_inventory_charges = checkout.inventory_charges
    final_asset_damage_charges = checkout.asset_damage_charges

    if bill_details:
        # Use charges from bill_details if record totals are 0
        if final_consumables_charges == 0:
            final_consumables_charges = bill_details.get('consumables_charges', 0)
        if final_inventory_charges == 0:
            final_inventory_charges = bill_details.get('inventory_charges', 0)
        if final_asset_damage_charges == 0:
            final_asset_damage_charges = bill_details.get('asset_damage_charges', 0)
        
        # Ensure root-level access for items in frontend
        if 'consumables_items' not in bill_details:
            # Try to pull from charges_breakdown or consumables_audit
            if 'charges_breakdown' in bill_details and 'consumables_items' in bill_details['charges_breakdown']:
                bill_details['consumables_items'] = bill_details['charges_breakdown']['consumables_items']
            elif 'consumables_audit' in bill_details and 'items' in bill_details['consumables_audit']:
                bill_details['consumables_items'] = bill_details['consumables_audit']['items']
        
        if 'asset_damages' not in bill_details or not isinstance(bill_details['asset_damages'], list):
            # If it's the object structure, move items to root list
            if isinstance(bill_details.get('asset_damages'), dict) and 'items' in bill_details['asset_damages']:
                bill_details['asset_damages'] = bill_details['asset_damages']['items']
            elif 'charges_breakdown' in bill_details and 'asset_damages' in bill_details['charges_breakdown']:
                bill_details['asset_damages'] = bill_details['charges_breakdown']['asset_damages']

    return {
        "id": checkout.id,
        "booking_id": checkout.booking_id,
        "package_booking_id": checkout.package_booking_id,
        "room_total": checkout.room_total,
        "food_total": final_food_total,
        "service_total": final_service_total,
        "package_total": checkout.package_total,
        "consumables_charges": final_consumables_charges,
        "inventory_charges": final_inventory_charges,
        "asset_damage_charges": final_asset_damage_charges,
        "tax_amount": checkout.tax_amount,
        "discount_amount": checkout.discount_amount,
        "grand_total": checkout.grand_total,
        "payment_method": checkout.payment_method,
        "payment_status": checkout.payment_status,
        "created_at": checkout.created_at.isoformat() if checkout.created_at else None,
        "guest_name": checkout.guest_name,
        "room_number": checkout.room_number,
        "room_numbers": room_numbers,
        "food_orders": food_orders,
        "services": services,
        "booking_details": booking_details,
        "bill_details": bill_details,
        "invoice_pdf_path": checkout.invoice_pdf_path
    }

@router.get("/active-rooms", response_model=List[dict])
def get_active_rooms(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), skip: int = 0, limit: int = 20, branch_id: int = Depends(get_branch_id)):

    """
    Returns a list of active rooms available for checkout with two options:
    1. Individual rooms (for single room checkout)
    2. Grouped bookings (for multiple room checkout together)
    Used to populate the checkout dropdown on the frontend.
    """
    try:
        # Fetch active bookings and package bookings with their rooms preloaded
        # Include both 'checked-in' and 'CHECKED-IN' status (case-insensitive matching)
        # Exclude 'booked' status - only show rooms that are already checked-in
        bookings_query = db.query(Booking).options(
            joinedload(Booking.booking_rooms).joinedload(BookingRoom.room)
        ).filter(
            func.lower(Booking.status).in_(['checked-in', 'checked_in', 'checked in'])
        )
        if branch_id is not None:
            bookings_query = bookings_query.filter(Booking.branch_id == branch_id)
        active_bookings = bookings_query.all()
        
        pkg_bookings_query = db.query(PackageBooking).options(

            joinedload(PackageBooking.rooms).joinedload(PackageBookingRoom.room)
        ).filter(
            func.lower(PackageBooking.status).in_(['checked-in', 'checked_in', 'checked in'])
        )
        if branch_id is not None:
            pkg_bookings_query = pkg_bookings_query.filter(PackageBooking.branch_id == branch_id)
        active_package_bookings = pkg_bookings_query.all()
        
        result = []
        
        # Debug: Log what we found
        # Debug logging removed

        
        # Helper function to safely get room number
        def get_room_number(link):
            """Safely extract room number from booking room link"""
            try:
                if not link:
                    return None
                if not link.room:
                    return None
                room_num = link.room.number
                if room_num is None or (isinstance(room_num, str) and room_num.strip() == ""):
                    return None
                return str(room_num).strip()
            except (AttributeError, Exception):
                return None
        
        # Process regular bookings
        for booking in active_bookings:
            # CRITICAL FIX: If booking is checked-in but rooms are "Available", repair the room status
            # This handles cases where room status was incorrectly set or changed
            # REFINED: Check for existing checkouts first to avoid repairing genuinely checked-out rooms
            booking_checkouts = db.query(Checkout).filter(Checkout.booking_id == booking.id).all()
            checked_out_rooms = set()
            for c in booking_checkouts:
                if c.room_number:
                    checked_out_rooms.update([r.strip() for r in c.room_number.split(',')])

            for link in booking.booking_rooms:
                if link.room and link.room.status and link.room.status.lower() == "available":
                    # Check if room is effectively checked out
                    if link.room.number in checked_out_rooms:
                        continue # Do not repair, it is correctly checked out
                    
                    # Booking is checked-in but room shows as Available - this is inconsistent
                    # Repair: Set room status to "Checked-in" to match booking status
                    # print(f"[DEBUG active-rooms] Repairing room {link.room.number}: status was 'Available', setting to 'Checked-in' (booking {booking.id} is checked-in)")

                    link.room.status = "Checked-in"
                    db.add(link.room)
            
            # Commit room status repairs before filtering
            db.commit()
            
            # Extract room numbers with proper null checks using helper function
            # Also filter out rooms that are already checked out (status = "Available")
            room_numbers = sorted([
                room_num for link in booking.booking_rooms 
                if (room_num := get_room_number(link)) is not None
                and link.room 
                and link.room.status 
                and link.room.status.lower() not in ["available", "checked-out", "checked_out", "checked out"]  # Exclude already checked-out rooms
            ])
            if room_numbers:
                # Add individual room options (one per room)
                for room_num in room_numbers:
                    result.append({
                        "room_number": room_num,
                        "room_numbers": [room_num],  # Single room
                        "guest_name": booking.guest_name,
                        "booking_id": booking.id,
                        "booking_type": "regular",
                        "checkout_mode": "single",
                        "display_label": f"Room {room_num} ({booking.guest_name})"
                    })
                
                # Add grouped booking option (all rooms together) - only if more than 1 room
                if len(room_numbers) > 1:
                    first_room = room_numbers[0]
                    result.append({
                        "room_number": first_room,  # Primary room for checkout API
                        "room_numbers": room_numbers,  # All rooms in this booking
                        "guest_name": booking.guest_name,
                        "booking_id": booking.id,
                        "booking_type": "regular",
                        "checkout_mode": "multiple",
                        "display_label": f"All Rooms in Booking #{booking.id}: {', '.join(room_numbers)} ({booking.guest_name})"
                    })
        
        # Process package bookings
        for pkg_booking in active_package_bookings:
            # CRITICAL FIX: If booking is checked-in but rooms are "Available", repair the room status
            # REFINED: Check for existing checkouts first
            pkg_checkouts = db.query(Checkout).filter(Checkout.package_booking_id == pkg_booking.id).all()
            pkg_checked_out_rooms = set()
            for c in pkg_checkouts:
                if c.room_number:
                    pkg_checked_out_rooms.update([r.strip() for r in c.room_number.split(',')])

            for link in pkg_booking.rooms:
                if link.room and link.room.status and link.room.status.lower() == "available":
                    # Check if room is effectively checked out
                    if link.room.number in pkg_checked_out_rooms:
                        continue # Do not repair, it is correctly checked out

                    # Booking is checked-in but room shows as Available - this is inconsistent
                    # Repair: Set room status to "Checked-in" to match booking status
                    # print(f"[DEBUG active-rooms] Repairing room {link.room.number}: status was 'Available', setting to 'Checked-in' (package booking {pkg_booking.id} is checked-in)")

                    link.room.status = "Checked-in"
                    db.add(link.room)
            
            # Commit room status repairs before filtering
            db.commit()
            
            # Extract room numbers with proper null checks using helper function
            # Also filter out rooms that are already checked out (status = "Available" or "available")
            # Include rooms with status "Checked-in", "Checked_in", "checked-in", etc.
            room_numbers = sorted([
                room_num for link in pkg_booking.rooms 
                if (room_num := get_room_number(link)) is not None
                and link.room 
                and link.room.status 
                and link.room.status.lower() not in ["available", "checked-out", "checked_out", "checked out"]  # Exclude already checked-out rooms
            ])
            if room_numbers:
                # Add individual room options (one per room)
                for room_num in room_numbers:
                    result.append({
                        "room_number": room_num,
                        "room_numbers": [room_num],  # Single room
                        "guest_name": pkg_booking.guest_name,
                        "booking_id": pkg_booking.id,
                        "booking_type": "package",
                        "checkout_mode": "single",
                        "display_label": f"Room {room_num} ({pkg_booking.guest_name})"
                    })
                
                # Add grouped booking option (all rooms together) - only if more than 1 room
                if len(room_numbers) > 1:
                    first_room = room_numbers[0]
                    result.append({
                        "room_number": first_room,  # Primary room for checkout API
                        "room_numbers": room_numbers,  # All rooms in this booking
                        "guest_name": pkg_booking.guest_name,
                        "booking_id": pkg_booking.id,
                        "booking_type": "package",
                        "checkout_mode": "multiple",
                        "display_label": f"All Rooms in Package #{pkg_booking.id}: {', '.join(room_numbers)} ({pkg_booking.guest_name})"
                    })
        
        # Sort by booking ID descending (most recent first)
        result = sorted(result, key=lambda x: x['booking_id'], reverse=True)
        
        # Debug: Log final result
        if len(result) == 0:
            pass # Debug prints removed

        
        return result[skip:skip+limit]
    except Exception as e:
        # Return empty list on error to prevent 500 response
        import traceback
        print(f"[ERROR active-rooms] Exception: {str(e)}")
        print(traceback.format_exc())
        return []

def _calculate_bill_for_single_room(db: Session, room_number: str, branch_id: int):
    """
    Calculates bill for a single room only, regardless of how many rooms are in the booking.
    """
    print(f"[DEBUG-BILL] Called _calculate_bill_for_single_room with room={room_number}, branch={branch_id}")
    # 1. Find the room
    q = db.query(Room).filter(Room.number == room_number)
    if branch_id is not None:
        q = q.filter(Room.branch_id == branch_id)
    room = q.first()
    
    if not room:
        room = db.query(Room).filter(func.trim(Room.number) == str(room_number).strip()).first()
        
    if not room:
        print(f"[DEBUG-BILL] Room {room_number} NOT FOUND in branch {branch_id}")
        # Probe: Does it exist in ANY branch?
        any_room = db.query(Room).filter(Room.number == room_number).first()
        if any_room:
            print(f"[DEBUG-BILL] Room {room_number} exists in branch {any_room.branch_id}, but not in {branch_id}")
        else:
            print(f"[DEBUG-BILL] Room {room_number} does not exist in any branch.")
        raise HTTPException(status_code=404, detail="Room not found.")
    
    # 2. Find the active parent booking (regular or package) linked to this room
    booking, is_package = None, False
    
    booking_link = (db.query(BookingRoom)
                    .join(Booking)
                    .options(joinedload(BookingRoom.booking))
                    .filter(BookingRoom.room_id == room.id, Booking.status.in_(['checked-in', 'checked_in', 'booked']))
                    .order_by(Booking.id.desc()).first())
    
    if booking_link:
        booking = booking_link.booking
        is_package = False
        if booking.status not in ['checked-in', 'checked_in', 'booked', 'checked-out', 'checked_out', 'checked out']:
            raise HTTPException(status_code=400, detail=f"Booking is not in a valid state for checkout. Current status: {booking.status}")
    else:
        # Check for active package booking BEFORE falling back to checked-out regular booking
        package_link = (db.query(PackageBookingRoom)
                        .join(PackageBooking)
                        .options(joinedload(PackageBookingRoom.package_booking))
                        .filter(PackageBookingRoom.room_id == room.id, PackageBooking.status.in_(['checked-in', 'checked_in', 'booked']))
                        .order_by(PackageBooking.id.desc()).first())
        
        if package_link:
            booking = package_link.package_booking
            is_package = True
            if booking.status not in ['checked-in', 'checked_in', 'booked', 'checked-out', 'checked_out', 'checked out']:
                raise HTTPException(status_code=400, detail=f"Package booking is not in a valid state for checkout. Current status: {booking.status}")
        else:
            # Fallback: Check for recently checked out regular booking
            booking_link = (db.query(BookingRoom)
                            .join(Booking)
                            .options(joinedload(BookingRoom.booking))
                            .filter(BookingRoom.room_id == room.id, Booking.status.in_(['checked-out', 'checked_out', 'checked out']))
                            .order_by(Booking.id.desc()).first())
            
            if booking_link:
                booking = booking_link.booking
                is_package = False
            else:
                # Fallback: Check for recently checked out package booking
                package_link = (db.query(PackageBookingRoom)
                                .join(PackageBooking)
                                .options(joinedload(PackageBookingRoom.package_booking))
                                .filter(PackageBookingRoom.room_id == room.id, PackageBooking.status.in_(['checked-out', 'checked_out', 'checked out']))
                                .order_by(PackageBooking.id.desc()).first())
                if package_link:
                    booking = package_link.package_booking
                    is_package = True
    
    if not booking:
        raise HTTPException(status_code=404, detail=f"No active or recent booking found for room {room_number}.")
    
    # 3. Calculate charges for THIS ROOM ONLY
    charges = BillBreakdown()
    
    # Calculate effective checkout date:
    # If actual checkout date (today) > booking.check_out (late checkout): use today
    # If actual checkout date (today) < booking.check_out (early checkout): use booking.check_out
    today = date.today()
    effective_checkout_date = max(today, booking.check_out)
    stay_days = max(1, (effective_checkout_date - booking.check_in).days)
    
    if is_package:
        # Check if this is a whole_property package
        package = booking.package if booking.package else None
        is_whole_property = False
        if package:
            # Check booking_type field
            booking_type = getattr(package, 'booking_type', None)
            if booking_type:
                is_whole_property = booking_type.lower() in ['whole_property', 'whole property']
            else:
                # Fallback: if no room_types specified, treat as whole_property (legacy packages)
                room_types = getattr(package, 'room_types', None)
                is_whole_property = not room_types or not room_types.strip()
        
        package_price = package.price if package else 0
        
        if is_whole_property:
            # For whole_property packages: package price is the total amount (not multiplied by days)
            # Note: For single room checkout, we still use the full package price
            # as it's a whole property package (all rooms included)
            charges.package_charges = package_price
            charges.room_charges = 0
        else:
            # For room_type packages: package price is per room, per night
            charges.package_charges = package_price * stay_days
            charges.room_charges = 0
    else:
        charges.package_charges = 0
        # For regular bookings: calculate room charges as dynamic priced days
        # Use existing dynamic pricing utility for accurate holiday/weekend rates
        dynamic_room_total = calculate_dynamic_booking_price(db, room.room_type_id, booking.check_in, effective_checkout_date, room_count=1)
        charges.room_charges = dynamic_room_total or ((room.price or 0) * stay_days)
        print(f"[DEBUG-BILL] Dynamic Pricing Result: {dynamic_room_total} (Base Fallback: {(room.price or 0) * stay_days})")
    
    # Determine start time for billing to include orders created before formal check-in
    # 1. Start with booking check-in date at 00:00:00
    check_in_datetime = datetime.combine(booking.check_in, datetime.min.time())
    
    # 2. Find the most recent checkout for this room to ensure we don't overlap with previous guest
    # Exclude checkouts for the current booking
    last_checkout_query = db.query(Checkout).filter(Checkout.room_number == room.number)
    
    if is_package:
        last_checkout_query = last_checkout_query.filter(Checkout.package_booking_id != booking.id)
    else:
        last_checkout_query = last_checkout_query.filter(Checkout.booking_id != booking.id)
        
    last_checkout = last_checkout_query.order_by(Checkout.checkout_date.desc()).first()
    
    if last_checkout and last_checkout.checkout_date:
        # If last checkout was after the calculated start time, use it as the new start time
        # This handles cases where previous guest checked out on the same day as new guest check-in
        if last_checkout.checkout_date > check_in_datetime:
            check_in_datetime = last_checkout.checkout_date
            print(f"[DEBUG] Adjusted check-in datetime based on previous checkout: {check_in_datetime}")
            
    print(f"[DEBUG] Using billing start time: {check_in_datetime}")

    # Get food and service charges for THIS ROOM ONLY, filtered by check-in datetime
    # Include ALL food orders (both billed and unbilled) - show paid ones with zero amount
    # Get food and service charges for THIS ROOM ONLY, filtered by check-in datetime
    # Include ALL food orders (both billed and unbilled) - show paid ones with zero amount
    if is_package:
         # For packages, prioritize the package_booking_id. 
         # We include ALL food orders for this package, across ANY room in the package.
         food_query = db.query(FoodOrderItem)\
                                .join(FoodOrder)\
                                .options(joinedload(FoodOrderItem.food_item), joinedload(FoodOrderItem.order))\
                                .filter(
                                    or_(
                                        FoodOrder.package_booking_id == booking.id,
                                        and_(
                                            FoodOrder.room_id == room.id, # Fallback for room-specific unlinked orders
                                            FoodOrder.package_booking_id == None,
                                            FoodOrder.booking_id == None,
                                            FoodOrder.created_at >= check_in_datetime
                                        )
                                    )
                                )
    else:
         food_query = db.query(FoodOrderItem)\
                                .join(FoodOrder)\
                                .options(joinedload(FoodOrderItem.food_item), joinedload(FoodOrderItem.order))\
                                .filter(
             or_(
                 FoodOrder.booking_id == booking.id,
                 and_(
                     FoodOrder.room_id == room.id,
                     FoodOrder.booking_id == None,
                     FoodOrder.package_booking_id == None,
                     FoodOrder.created_at >= check_in_datetime
                 )
             )
         )
    all_food_order_items = food_query.all()
    
    # Separate food orders by billing status:
    # - Unbilled: billing_status is None, "unbilled", or "unpaid" (add to bill)
    # - Paid: billing_status is "paid" (show as paid, don't add to bill)
    # - Billed: billing_status is "billed" (already billed, show as paid)
    unbilled_food_order_items = [item for item in all_food_order_items 
                                 if not item.order or item.order.billing_status in ["unbilled", "unpaid"] or item.order.billing_status is None]
    paid_food_order_items = [item for item in all_food_order_items 
                            if item.order and item.order.billing_status == "paid"]
    billed_food_order_items = [item for item in all_food_order_items 
                               if item.order and item.order.billing_status == "billed"]
    
    # Get ALL assigned services for this room (both billed and unbilled)
    # Similar to food items, we show billed services as "Paid" with zero charge
    # Use booking's actual check_in date as a fallback start (not the adjusted check_in_datetime
    # which may have been pushed forward by a previous guest's checkout)
    booking_check_in_datetime = datetime.combine(booking.check_in, datetime.min.time())
    booking_check_out_datetime = datetime.combine(booking.check_out, datetime.max.time())

    if is_package:
         # For packages, include ALL services linked to this package booking across ALL rooms
         svc_query = db.query(AssignedService).options(joinedload(AssignedService.service)).filter(
             or_(
                 AssignedService.package_booking_id == booking.id,
                 and_(
                     AssignedService.room_id == room.id,
                     AssignedService.package_booking_id == None,
                     AssignedService.booking_id == None,
                     AssignedService.assigned_at >= booking_check_in_datetime,
                     AssignedService.assigned_at <= booking_check_out_datetime
                 )
             )
         )
    else:
         svc_query = db.query(AssignedService).options(joinedload(AssignedService.service)).filter(
             AssignedService.room_id == room.id
         ).filter(
             or_(
                 AssignedService.booking_id == booking.id,
                 and_(
                     AssignedService.booking_id == None,
                     AssignedService.package_booking_id == None,
                     AssignedService.assigned_at >= booking_check_in_datetime,
                     AssignedService.assigned_at <= booking_check_out_datetime
                 )
             )
         )
         
    all_assigned_services = svc_query.all()
    
    # Separate unbilled, paid-at-counter, and billed services
    unbilled_services = [ass for ass in all_assigned_services if ass.billing_status in ["unbilled", "unpaid"] or ass.billing_status is None]
    paid_services = [ass for ass in all_assigned_services if ass.billing_status == "paid"]
    billed_services = [ass for ass in all_assigned_services if ass.billing_status == "billed"]
    
    # Calculate charges: only unbilled items contribute to charges
    from app.utils.food_pricing import get_food_item_price_at_time
    
    charges.food_charges = sum(
        (item.quantity * get_food_item_price_at_time(
            item.food_item, 
            item.order.created_at if item.order else None,
            item.order.order_type if item.order else "dine_in"
        )) 
        if (item.food_item and (not item.order or (item.order.amount or 0) > 0)) else 0 
        for item in unbilled_food_order_items
    )
    charges.service_charges = sum(ass.override_charges if ass.override_charges is not None else ass.service.charges for ass in unbilled_services)
    
    # Include ALL food items in the list with payment status
    charges.food_items = []
    
    # Add unbilled items with their actual amounts
    # Add unbilled items with their actual amounts
    for item in unbilled_food_order_items:
        if item.food_item:
            # Check if order is complimentary (amount is 0)
            is_complimentary = item.order and item.order.amount == 0
            
            # HIDE complimentary items for package bookings to keep bill guest-friendly
            if is_package and is_complimentary:
                continue
                
            # Use same pricing logic for breakdown
            current_item_price = get_food_item_price_at_time(
                item.food_item, 
                item.order.created_at if item.order else None,
                item.order.order_type if item.order else "dine_in"
            )
            item_amount = 0.0 if is_complimentary else (item.quantity * current_item_price)
            
            charges.food_items.append({
                "item_name": item.food_item.name, 
                "quantity": item.quantity, 
                "amount": item_amount,
                "is_paid": False,
                "payment_status": "Complimentary" if is_complimentary else "Unpaid"
            })
    
    # Add paid items (paid at delivery) with payment details
    for item in paid_food_order_items:
        if item.food_item and item.order:
            charges.food_items.append({
                "item_name": item.food_item.name, 
                "quantity": item.quantity, 
                "amount": 0.0,  # Don't add to bill
                "is_paid": True,
                "payment_status": f"PAID ({item.order.payment_method or 'cash'})",
                "payment_method": item.order.payment_method,
                "payment_time": item.order.payment_time.isoformat() if item.order.payment_time else None,
                "gst_amount": item.order.gst_amount,
                "total_with_gst": item.order.total_with_gst
            })
    
    # Add billed items (already in previous bills)
    for item in billed_food_order_items:
        if item.food_item:
            charges.food_items.append({
                "item_name": item.food_item.name, 
                "quantity": item.quantity, 
                "amount": 0.0,
                "is_paid": True,
                "payment_status": "Previously Billed"
            })
    
    # Include ALL service items with payment status (similar to food items)
    charges.service_items = []
    
    # Add unbilled services with their actual charges
    for ass in unbilled_services:
        charges.service_items.append({
            "service_name": ass.service.name, 
            "charges": ass.override_charges if ass.override_charges is not None else ass.service.charges,
            "is_paid": False,
            "payment_status": "Unpaid"
        })
    
    # Add paid-at-counter services (paid when service was rendered)
    for ass in paid_services:
        charges.service_items.append({
            "service_name": ass.service.name, 
            "charges": 0.0,  # Don't add to bill - already paid
            "is_paid": True,
            "payment_status": "PAID (at counter)"
        })
    
    # Add billed services with zero charge (marked as paid)
    for ass in billed_services:
        charges.service_items.append({
            "service_name": ass.service.name, 
            "charges": 0.0,  # Don't add to bill
            "is_paid": True,
            "payment_status": "Previously Billed"
        })
    
    # Calculate Consumables Charges from CheckoutRequest
    
    if is_package:
        checkout_request = db.query(CheckoutRequestModel).filter(
            CheckoutRequestModel.package_booking_id == booking.id,
            CheckoutRequestModel.room_number == room_number,
            CheckoutRequestModel.status == "completed"
        ).order_by(CheckoutRequestModel.id.desc()).first()
    else:
        checkout_request = db.query(CheckoutRequestModel).filter(
            CheckoutRequestModel.booking_id == booking.id,
            CheckoutRequestModel.room_number == room_number,
            CheckoutRequestModel.status == "completed"
        ).order_by(CheckoutRequestModel.id.desc()).first()
        
    if checkout_request:
        print(f"[BILLING_DEBUG] Using Checkout Request ID: {checkout_request.id} (Status: {checkout_request.status})")
    else:
        print(f"[BILLING_DEBUG] No completed checkout request found for Room {room_number} (Booking {booking.id})")
        
    import re
    processed_ids = set()
    seen_item_keys = set()
    
    # 1. PRE-SCAN STOCK ISSUES for Rental Prices and Asset Status
    # This ensures we know which items are rentals BEFORE processing the audit data
    rental_map = {} # item_id -> {rental_price: float, is_payable: bool, is_fixed: bool}
    
    if room.inventory_location_id:
        room_issues = (db.query(StockIssueDetail)
                       .join(StockIssue)
                       .filter(StockIssue.destination_location_id == room.inventory_location_id)
                       .all())
        for d in room_issues:
            iid = int(d.item_id)
            if iid not in rental_map:
                rental_map[iid] = {
                    "rental_price": float(d.rental_price or 0.0),
                    "is_payable": getattr(d, 'is_payable', False),
                    "is_asset": d.item.is_asset_fixed if d.item else False
                }
            else:
                # Keep highest rental price seen or most recent
                if float(d.rental_price or 0.0) > 0:
                    rental_map[iid]["rental_price"] = max(rental_map[iid]["rental_price"], float(d.rental_price or 0.0))
    
    print(f"DEBUG BILL CALC SINGLE START Room {room_number}")
    
    # 2. Process Audit Data with composite key (item_id, is_rentable, is_fixed_asset)
    aggregated_audit = {} # (iid, is_rent, is_fixed) -> aggregated_item_data
    generic_assets = [] # Items without item_id
    
    if checkout_request and checkout_request.inventory_data:
        for item_data in checkout_request.inventory_data:
            iid = int(item_data.get('item_id') or 0)
            if not iid:
                generic_assets.append(item_data)
                continue
            
            # Use explicit flags passed from audit
            is_rent = item_data.get('is_rentable', False)
            is_fixed = item_data.get('is_fixed_asset', False)
            
            # Group by (Item ID, is_rentable) to separate rented counts from fixed assets
            audit_key = (iid, is_rent)
            
            if audit_key not in aggregated_audit:
                aggregated_audit[audit_key] = {
                    "item_id": iid,
                    "is_rentable": is_rent,
                    "is_fixed_asset": False,
                    "used_qty": 0.0,
                    "damage_qty": 0.0,
                    "missing_qty": 0.0,
                    "allocated_stock": 0.0,
                    "provided_bad_charge": 0.0,
                    "provided_usage_charge": 0.0, # Separate usage from bad charges
                    "complimentary_qty": 0.0
                }
            
            # OR logic for fixed flag within this specific (iid, is_rent) group
            if is_fixed: aggregated_audit[audit_key]["is_fixed_asset"] = True
            
            # Combine quantities
            aggregated_audit[audit_key]["used_qty"] += float(item_data.get('used_qty') or 0)
            aggregated_audit[audit_key]["damage_qty"] += float(item_data.get('damage_qty') or 0)
            aggregated_audit[audit_key]["missing_qty"] += float(item_data.get('missing_qty') or 0)
            
            # SEPARATE USAGE VS DAMAGE CHARGES
            aggregated_audit[audit_key]["provided_usage_charge"] += float(item_data.get('total_charge') or 0)
            aggregated_audit[audit_key]["provided_bad_charge"] += float(item_data.get('damage_charge') or item_data.get('missing_item_charge') or 0)
            
            # Use max for limit to prevent double counting of master limit across multiple batches
            aggregated_audit[audit_key]["complimentary_qty"] = max(aggregated_audit[audit_key]["complimentary_qty"], float(item_data.get('complimentary_qty') or item_data.get('complimentary_limit') or 0))
            aggregated_audit[audit_key]["allocated_stock"] += float(item_data.get('allocated_stock') or 0)

    for (item_id, is_rentable_audit), item_data in aggregated_audit.items():
        item_id = item_data['item_id']
        used_qty = item_data['used_qty']
        damage_qty = item_data['damage_qty']
        missing_qty = item_data['missing_qty']
        allocated_stock = item_data['allocated_stock']
        
        # EXPLICIT FLAGS FROM AUDIT (already separated by key)
        is_fixed_audit = item_data['is_fixed_asset']
        
        inv_item = db.query(InventoryItem).options(joinedload(InventoryItem.category)).filter(InventoryItem.id == item_id).first()
        if not inv_item: continue

        processed_ids.add(item_id)
        clean_name = re.sub(r'\s*\(\s*[xX]\d+[^)]*\)', '', inv_item.name).strip()
        
        # Consistent key for both audit and fallback sections
        item_key = f"{clean_name.lower()}_{item_id}"
        
        # Display check: separation by rental status
        display_key = f"{item_key}_{is_rentable_audit}"
        if display_key in seen_item_keys: continue
        seen_item_keys.add(display_key)
        
        # Also mark the base item_key as seen to suppress fallback logic in section 5
        seen_item_keys.add(item_key)
        
        # Master Prices
        selling_price = float(inv_item.selling_price or 0.0)
        # Priority: Purchase Price + GST as requested by user for fixed assets/rentals
        # Safely handle GST: If it's an asset but GST is 0, assume standard 12% for replacement cost
        item_gst = float(inv_item.gst_rate or 0.0)
        
        # Aggressive asset check for GST fallback
        asset_names = ["tv", "towel", "linen", "kettle", "fridge", "ac", "remote", "bulb", "fan", "furniture", "chair", "table", "bed"]
        is_known_asset = inv_item.is_asset_fixed or any(an in clean_name.lower() for an in asset_names)
        
        # Consumables Pricing Fix: Prioritize selling_price (guest price) over unit_price (purchase price/cost)
        selling_price_base = float(inv_item.selling_price or 0.0)
        cost_price_with_gst = float(inv_item.unit_price or 0.0) * (1.0 + item_gst / 100.0)
        
        # Priority: 1. Selling Price, 2. Cost Price + GST
        replacement_price = selling_price_base if selling_price_base > 0 else (cost_price_with_gst if cost_price_with_gst > 0 else 0.0)
        
        # Safety fallback for tax-exclusive prices if everything is still zero
        if replacement_price == 0 and selling_price_base > 0:
             replacement_price = selling_price_base * 1.12
        elif replacement_price == 0 and cost_price_with_gst > 0:
             replacement_price = cost_price_with_gst
        
        total_item_charge = 0.0
        
        # Classification RE-EVALUATED
        rm = rental_map.get(item_id, {})
        has_rental_fee = rm.get("rental_price", 0) > 0
        is_in_rental_cat = "rental" in (inv_item.category.name if inv_item.category else "").lower()
        
        is_amenity = any(kw in clean_name.lower() for kw in ["water", "soap", "shampoo", "toothpaste", "vanity"])
        # Determine if it's an asset based on category name
        asset_keywords = ["linen", "electronic", "furniture", "asset", "fixed", "appliance", "electrical", "fixture", "towel", "bedsheet"]
        is_asset_category = any(kw in (inv_item.category.name if inv_item.category else "").lower() for kw in asset_keywords)
        
        # Determine if it's a consumable based on category name
        consumable_keywords = ["food", "drink", "beverage", "amenity", "toiletries", "mini bar", "consumable", "provision"]
        is_consumable_category = any(kw in (inv_item.category.name if inv_item.category else "").lower() for kw in consumable_keywords) or is_amenity

        # Determine if THIS specific batch is rentable
        # Logic: Category contains "Rent" OR explicitly marked in audit.
        is_rentable = is_rentable_audit or "rental" in (inv_item.category.name if inv_item.category else "").lower()
        
        # If it's an asset category but NOT rentable in the audit/category, we treat it as a standard asset
        if is_asset_category and not ("rental" in (inv_item.category.name if inv_item.category else "").lower() or is_rentable_audit):
            is_rentable = False
            
        # OVERRIDE: Consumables should NEVER be rentable.
        if is_consumable_category:
            is_rentable = False
            
        # Determine if THIS specific batch is a fixed asset
        is_fixed_asset = is_fixed_audit or inv_item.is_asset_fixed or is_asset_category 
        
        # 3. Calculate Rental Charge (Usage)
        usage_charge = 0.0
        # For non-rentable fixed asset batches, unit price is 0 (standard room items)
        rental_unit_price = rm.get("rental_price", 0) if is_rentable else 0.0
        if rental_unit_price == 0 and is_rentable:
             rental_unit_price = selling_price
        # Also try unit_price from audit data as a further fallback for rentals
        if rental_unit_price == 0 and is_rentable:
             rental_unit_price = float(item_data.get('unit_price') or 0)
        
        # Enter the usage block if there are any quantities OR a pre-calculated charge
        provided_usage_for_gate = float(item_data.get('provided_usage_charge') or 0)
        if used_qty > 0 or allocated_stock > 0 or missing_qty > 0 or provided_usage_for_gate > 0:
            limit = float(item_data.get('complimentary_qty', 0))
            
            # RE-CALCULATION FOR EXISTING BAD DATA
            if limit == 0 and checkout_request.booking_id:
                try:
                    # Infer room location id from room number if strictly needed or rely on 0
                    current_room_obj = db.query(Room).filter(Room.number == room_number).first()
                    current_booking_obj = db.query(Booking).filter(Booking.id == checkout_request.booking_id).first()
                    if current_room_obj and current_booking_obj and current_room_obj.inventory_location_id:
                         cutoff_date = current_booking_obj.check_in - timedelta(days=1)
                         
                         comp_issued_qty = (db.query(func.sum(StockIssueDetail.issued_quantity))
                            .join(StockIssue)
                            .filter(
                                StockIssue.destination_location_id == current_room_obj.inventory_location_id,
                                StockIssueDetail.item_id == item_id,
                                StockIssue.issue_date >= cutoff_date,
                                or_(StockIssueDetail.is_payable == False, StockIssueDetail.is_payable == None)
                            )
                            .scalar()) or 0.0
                         if comp_issued_qty > 0:
                            limit = float(comp_issued_qty)
                            # print(f"DEBUG RE-CALC LIMIT: Item {inv_item.name} Limit increased to {limit} from StockHistory")
                except: pass

            # Fallback for limit
            if limit == 0:
                 limit = float(inv_item.complimentary_limit or 0)
            
            # 3. Calculate Rental / Usage Charge
            if is_rentable:
                # Group issues by price for clear billing breakdown
                price_groups = {} # price -> qty
                
                try:
                    current_room_obj = db.query(Room).filter(Room.number == room_number).first()
                    if current_room_obj and current_room_obj.inventory_location_id:
                        rental_details = db.query(StockIssueDetail).join(StockIssue).filter(
                            StockIssue.destination_location_id == current_room_obj.inventory_location_id,
                            StockIssueDetail.item_id == item_id,
                            StockIssueDetail.rental_price > 0,
                            StockIssue.issue_date >= (getattr(booking, 'checked_in_at', None) or booking.check_in)
                        ).all()
                        
                        for detail in rental_details:
                            p = float(detail.rental_price)
                            price_groups[p] = price_groups.get(p, 0.0) + float(detail.issued_quantity)
                except Exception as e:
                    print(f"[BILLING ERROR] Multi-price grouping failed for {clean_name}: {e}")
                
                # Calculate from issues
                total_calc_charge = 0.0
                for price, group_qty in price_groups.items():
                    total_calc_charge += group_qty * price * stay_days
                
                if total_calc_charge == 0 and provided_usage_for_gate > 0:
                    # Clear price groups and use the fallback
                    price_groups = {}
                    price = rental_unit_price if rental_unit_price > 0 else float(item_data.get('unit_price') or 0.0)
                    if price > 0:
                         price_groups[price] = provided_usage_for_gate / (price * stay_days) if stay_days > 0 else allocated_stock
                    else:
                         price_groups[0.0] = allocated_stock

                for price, group_qty in price_groups.items():
                    u_charge = group_qty * price * stay_days
                    
                    # Note for guest if rent is waived or if it's a stay-related asset
                    item_notes = "Rental"
                    if (damage_qty + missing_qty) > 0 and u_charge == 0:
                        item_notes = "Rent waived (Damaged/Missing)"
                    
                    charges.inventory_usage.append({
                        "date": checkout_request.completed_at or datetime.now(),
                        "item_name": clean_name + (f" @ {price}" if len(price_groups) > 1 else ""),
                        "category": inv_item.category.name if inv_item.category else "Rental",
                        "quantity": group_qty,
                        "unit": inv_item.unit or "pcs",
                        "rental_price": price,
                        "rental_charge": u_charge,
                        "is_rental": True,
                        "is_payable": True,
                        "notes": item_notes
                    })
                    # Add to total rental charges
                    if u_charge > 0:
                        charges.inventory_charges = (charges.inventory_charges or 0) + u_charge
            
            elif is_amenity or (getattr(inv_item, 'is_sellable_to_guest', False) or limit > 0):
                # Consumables / Amenities
                total_consumed = used_qty 
                usage_charge, replacement_price, chargeable_qty = calculate_consumable_charge(inv_item, total_consumed, limit_from_audit=limit)
                # Since missing is handled in usage_charge for these items, we zero it out to prevent double-charging in bad_charge logic
                missing_qty = 0 
                # Store for display logic below
                total_item_charge = usage_charge
            
            # 4. Calculate Damage / Missing Charge (BAD CHARGE)
            calc_bad_charge = (damage_qty + missing_qty) * replacement_price
            provided_bad_charge = float(item_data.get('provided_bad_charge') or 0)
            
            if (is_amenity or (not is_rentable and not is_fixed_asset)) and damage_qty == 0 and missing_qty == 0:
                bad_charge = 0.0
            else:
                bad_charge = max(calc_bad_charge, provided_bad_charge)
            
            # FORCE BAD CHARGE for Damaged Fixed Assets if calculated as 0 but damage exists
            if is_fixed_asset and (damage_qty > 0 or missing_qty > 0) and bad_charge == 0:
                 bad_charge = (damage_qty + missing_qty) * replacement_price

            # 5. Display Logic for Non-Rentals (Fixed Assets / Consumables)
            if is_fixed_asset and not is_rentable:
                # Pure Fixed Asset Logic
                if (damage_qty + missing_qty) > 0:
                    charges.fixed_assets.append({
                        "item_name": clean_name,
                        "status": "Damaged" if damage_qty > 0 else "Missing",
                        "quantity": damage_qty + missing_qty,
                        "notes": f"Verified from audit"
                    })
    
                # Add to Asset Damages if there is damage OR if there is a bad_charge (manual charge)
                if bad_charge > 0 or damage_qty > 0 or missing_qty > 0:
                    final_bad_charge = bad_charge
                    if final_bad_charge == 0:
                        safe_price = replacement_price
                        if safe_price == 0:
                            safe_price = float(inv_item.unit_price or 0) * 1.5
                        
                        if safe_price == 0: safe_price = 50.0
                        final_bad_charge = (damage_qty + missing_qty) * safe_price
    
                    if final_bad_charge > 0:
                        charges.asset_damage_charges = (charges.asset_damage_charges or 0) + final_bad_charge
                        label_suffix = " (Damaged)" if damage_qty > 0 else " (Missing)"
                        if damage_qty > 0 and missing_qty > 0: label_suffix = " (Damaged/Missing)"
                        charges.asset_damages.append({
                            "item_name": f"{clean_name}{label_suffix}",
                            "replacement_cost": final_bad_charge,
                            "notes": f"Damaged: {damage_qty}, Missing: {missing_qty}"
                        })
            elif not is_rentable:
                # Consumables Display
                if is_asset_category:
                    pass # Already handled or skipped
                else:
                        total_qty = used_qty 
                        if allocated_stock > 0:
                            total_qty = min(used_qty, allocated_stock)
                        
                        if total_qty > 0 or total_item_charge > 0:
                            label = clean_name
                            if damage_qty > 0:
                                label += f" ({int(total_qty - damage_qty)} Used, {int(damage_qty)} Damaged)"
                            
                            charges.consumables_charges = (charges.consumables_charges or 0) + total_item_charge
                            charges.consumables_items.append({
                                "date": checkout_request.completed_at or datetime.now(),
                                "item_id": item_id,
                                "item_name": label,
                                "actual_consumed": total_qty,
                                "complimentary_limit": limit,
                                "charge_per_unit": total_item_charge / total_qty if total_qty > 0 else replacement_price,
                                "total_charge": total_item_charge
                            })

    # 4.5. Process Generic Assets (No item_id)
    for asset_data in generic_assets:
        replacement_cost = float(asset_data.get('replacement_cost', 0))
        if replacement_cost > 0:
            item_name = asset_data.get('item_name', 'Damaged Asset')
            charges.asset_damage_charges = (charges.asset_damage_charges or 0) + replacement_cost
            charges.asset_damages.append({
                "item_name": f"{item_name} (Damaged)",
                "replacement_cost": replacement_cost,
                "notes": asset_data.get('notes', 'Asset damage')
            })


    # 5. Stock Issues NOT in Audit
    # STRICT FILTER: Only include stock issues occurring ON or AFTER the billing start time.
    # This excludes "Room Preparation" stock (pre-stocked mini-bar) from automatically appearing as consumed.
    # Consumption of pre-stocked items must be confirmed via Checkout Verification (Audit).
    # Items issued DURING the stay are considered direct sales/requests and are included.
    stock_issues = (db.query(StockIssue)
                    .options(joinedload(StockIssue.details).joinedload(StockIssueDetail.item))
                    .filter(StockIssue.destination_location_id == room.inventory_location_id,
                            StockIssue.issue_date >= check_in_datetime)
                    .all())
    
    # Calculate potential booking human-readable IDs for notes matching
    from app.utils.booking_id import format_display_id
    possible_ids = [
        format_display_id(booking.id, branch_id=branch_id, is_package=is_package),
        f"BK-{str(booking.id).zfill(6)}", 
        f"PK-{str(booking.id).zfill(6)}"
    ]
    if getattr(booking, 'display_id', None):
        possible_ids.append(booking.display_id)

    for issue in stock_issues:
        # Cross-validate notes for ANY Booking ID mention
        issue_notes_upper = (issue.notes or "").upper()
        has_any_bk = "BK-" in issue_notes_upper or "PK-" in issue_notes_upper or "BOOKING " in issue_notes_upper or "FOR BK" in issue_notes_upper
        
        if has_any_bk:
            # If notes mention a booking but NOT ours, skip it
            if not any(pid in issue_notes_upper for pid in possible_ids):
                print(f"[BILLING] Skipping StockIssue {issue.issue_number} - belongs to different booking: {issue.notes}")
                continue

        for detail in issue.details:
            if not detail.item: continue
            clean_name = re.sub(r'\s*\(\s*[xX]\d+[^)]*\)', '', detail.item.name).strip()
            item_key = f"{clean_name.lower()}_{detail.item_id}"
            
            if (int(detail.item_id) in processed_ids) or (item_key in seen_item_keys): continue
            
            r_price = float(detail.rental_price or 0.0)
            u_charge = 0.0
            
            # Heuristic Fix: Check if this item is already listed in asset damages
            # If so, do not charge rent here (Stock Issue Fallback)
            is_damaged_in_bill = False
            for dmg in charges.asset_damages:
                # dmg['item_name'] usually has suffix " (Damaged)" or " (Missing)"
                if clean_name in dmg['item_name']:
                     is_damaged_in_bill = True
                     break
            
            if is_damaged_in_bill:
                print(f"[BILLING] Waiving fallback rent for {clean_name} as it is in damages")
                u_charge = 0.0
            elif r_price > 0:
                # FIX: Multiply by stay duration
                u_charge = r_price * detail.issued_quantity * stay_days
            elif getattr(detail, 'is_payable', False):
                p = float(detail.item.selling_price or detail.item.unit_price or 0.0)
                u_charge = p * detail.issued_quantity

            # Check for manual damage mark in DB (if not in audit)
            bad_charge = 0.0
            if getattr(detail, 'is_damaged', False):
                s_price = float(detail.item.selling_price or 0.0)
                rep_price = s_price if s_price > 0 else (float(detail.item.unit_price or 0.0) * (1.0 + float(detail.item.gst_rate or 0.0) / 100.0))
                bad_charge = detail.issued_quantity * rep_price
                print(f"[BILLING] Picked up manually marked damage for {detail.item.name}: {bad_charge}")

            if u_charge > 0 or bad_charge > 0:
                processed_ids.add(int(detail.item_id))
                seen_item_keys.add(item_key)

            # Classification RE-EVALUATED for Fallback Section
            asset_keywords = ["linen", "electronic", "furniture", "asset", "fixed", "appliance", "electrical", "fixture", "towel", "bedsheet"]
            is_fixed_master = detail.item.is_asset_fixed or any(kw in (detail.item.category.name if detail.item.category else "").lower() for kw in asset_keywords)
            
            consumable_keywords = ["food", "drink", "beverage", "amenity", "toiletries", "mini bar", "consumable", "provision"]
            is_consumable_master = any(kw in (detail.item.category.name if detail.item.category else "").lower() for kw in consumable_keywords)
            
            is_rentable = r_price > 0 and not is_consumable_master
            is_fixed_asset = is_fixed_master
            
            if is_rentable:
                charges.inventory_usage.append({
                    "date": issue.issue_date,
                    "item_name": clean_name,
                    "category": detail.item.category.name if detail.item.category else "Rental",
                    "quantity": detail.issued_quantity,
                    "unit": detail.unit or "pcs",
                    "rental_price": r_price,
                    "rental_charge": u_charge,
                    "is_rental": True,
                    "is_payable": u_charge > 0,
                    "notes": "Issued stock (fallback)"
                })
                if u_charge > 0:
                    charges.inventory_charges = (charges.inventory_charges or 0) + u_charge
            elif is_consumable_master or (not is_fixed_asset and getattr(detail, 'is_payable', False)):
                 # Consumable Fallback
                 if u_charge > 0 or bad_charge > 0:
                    charges.consumables_charges = (charges.consumables_charges or 0) + u_charge
                    charges.consumables_items.append({
                        "date": issue.issue_date,
                        "item_id": detail.item_id,
                        "item_name": f"{clean_name} (Auto-detected)",
                        "actual_consumed": detail.issued_quantity,
                        "complimentary_limit": detail.item.complimentary_limit or 0,
                        "charge_per_unit": u_charge / detail.issued_quantity if detail.issued_quantity > 0 else 0.0,
                        "total_charge": u_charge
                    })
            elif is_fixed_asset:
                 # Only show if damaged in fallback
                 if bad_charge > 0:
                    charges.fixed_assets.append({
                        "item_name": clean_name,
                        "status": "Logged as Damaged",
                        "quantity": detail.issued_quantity,
                        "notes": "Pre-marked issue"
                    })
                
            if bad_charge > 0:
                charges.asset_damage_charges = (charges.asset_damage_charges or 0) + bad_charge
                charges.asset_damages.append({
                    "item_name": f"{clean_name} (Damaged - Pre-marked)",
                    "replacement_cost": bad_charge,
                    "notes": "Logged in system"
                })

                
    # Summary & GST
    # Room GST Logic (Standard Tiered)
    # Standard: 12% if < 7500, 18% if >= 7500
    room_gst_rate = 0.12 if (room.price or 0) < 7500 else 0.18
    # Keep 5% only for extremely budget rooms if that was the intent, but user instructions say 12%
    if (room.price or 0) < 1000: room_gst_rate = 0.12 # Assuming no 0% category for simplicity here
    
    charges.room_gst = (charges.room_charges or 0) * room_gst_rate
    
    # Package GST Logic (Tiered)
    if is_package:
        p_price = package.price if package else 0
        p_rate = 0
        if is_whole_property:
             p_rate = p_price / max(1, stay_days)
        else:
             p_rate = p_price
        
        pkg_gst_rate = 0.18
        if p_rate < 5000: pkg_gst_rate = 0.05
        elif p_rate <= 7500: pkg_gst_rate = 0.12
        charges.package_gst = (charges.package_charges or 0) * pkg_gst_rate
    else:
        charges.package_gst = 0

    charges.food_gst = (charges.food_charges or 0) * 0.05
    charges.service_gst = (charges.service_charges or 0) * 0.05
    charges.consumables_gst = (charges.consumables_charges or 0) * 0.05
    charges.inventory_gst = (charges.inventory_charges or 0) * 0.05
    charges.asset_damage_gst = 0.0 # Removed as per request (was 0.05)
    
    # Total calculation
    charges.total_gst = sum([charges.room_gst or 0, charges.food_gst or 0, charges.service_gst or 0, charges.package_gst or 0, charges.consumables_gst or 0, charges.inventory_gst or 0, charges.asset_damage_gst or 0])
    charges.total_due = sum([charges.room_charges or 0, charges.food_charges or 0, charges.service_charges or 0, charges.package_charges or 0, charges.consumables_charges or 0, charges.inventory_charges or 0, charges.asset_damage_charges or 0])


    
    # Add advance deposit info to charges
    charges.advance_deposit = getattr(booking, 'advance_deposit', 0.0) or 0.0
    
    number_of_guests = getattr(booking, 'number_of_guests', 1)
    
    return {
        "booking": booking, "room": room, "charges": charges,
        "is_package": is_package, "stay_nights": stay_days, "number_of_guests": number_of_guests,
        "effective_checkout_date": effective_checkout_date
    }

def _calculate_bill_for_entire_booking(db: Session, room_number: str, branch_id: int):
    """
    Core logic: Finds an entire booking from a single room number and calculates the total bill
    for all associated rooms and services.
    """
    # 1. Find the initial room to identify the parent booking
    initial_room = db.query(Room).filter(Room.number == room_number, Room.branch_id == branch_id).first()
    if not initial_room:
        raise HTTPException(status_code=404, detail="Initial room not found.")

    # 2. Find the active parent booking (regular or package) linked to this room
    booking, is_package = None, False
    
    # Eagerly load the booking relationship to avoid extra queries
    # Order by descending ID to get the MOST RECENT booking for the room first.
    # Handle both 'checked-in' and 'checked_in' status formats
    booking_link = (db.query(BookingRoom)
                    .join(Booking)
                    .options(joinedload(BookingRoom.booking)) # Eager load the booking
                    .filter(BookingRoom.room_id == initial_room.id, Booking.status.in_(['checked-in', 'checked_in', 'booked']))
                    .order_by(Booking.id.desc()).first())

    if booking_link:
        booking = booking_link.booking
        is_package = False
        # Validate booking status before proceeding
        if booking.status not in ['checked-in', 'checked_in', 'booked', 'checked-out', 'checked_out', 'checked out']:
            raise HTTPException(status_code=400, detail=f"Booking is not in a valid state for checkout. Current status: {booking.status}")
    else:
        # Check for active package booking BEFORE falling back to checked-out regular booking
        package_link = (db.query(PackageBookingRoom)
                        .join(PackageBooking)
                        .options(joinedload(PackageBookingRoom.package_booking)) # Eager load the booking
                        .filter(PackageBookingRoom.room_id == initial_room.id, PackageBooking.status.in_(['checked-in', 'checked_in', 'booked']))
                        .order_by(PackageBooking.id.desc()).first())
        
        if package_link:
            booking = package_link.package_booking
            is_package = True
            # Validate booking status before proceeding
            if booking.status not in ['checked-in', 'checked_in', 'booked', 'checked-out', 'checked_out', 'checked out']:
                raise HTTPException(status_code=400, detail=f"Package booking is not in a valid state for checkout. Current status: {booking.status}")
        else:
            # Fallback: Check for recently checked out regular booking
            booking_link = (db.query(BookingRoom)
                            .join(Booking)
                            .options(joinedload(BookingRoom.booking))
                            .filter(BookingRoom.room_id == initial_room.id, Booking.status.in_(['checked-out', 'checked_out', 'checked out']))
                            .order_by(Booking.id.desc()).first())
            
            if booking_link:
                booking = booking_link.booking
                is_package = False
            else:
                # Fallback: Check for recently checked out package booking
                package_link = (db.query(PackageBookingRoom)
                                .join(PackageBooking)
                                .options(joinedload(PackageBookingRoom.package_booking))
                                .filter(PackageBookingRoom.room_id == initial_room.id, PackageBooking.status.in_(['checked-out', 'checked_out', 'checked out']))
                                .order_by(PackageBooking.id.desc()).first())
                if package_link:
                    booking = package_link.package_booking
                    is_package = True

    if not booking:
        raise HTTPException(status_code=404, detail="No active or recent booking found for this room.")

    # 3. Get ALL rooms and their IDs associated with the found booking
    all_rooms = []
    if is_package:
        # For package bookings, the relationship is `booking.rooms` -> `PackageBookingRoom` -> `room`
        all_rooms = [link.room for link in booking.rooms]
    else:
        # For regular bookings, the relationship is `booking.booking_rooms` -> `BookingRoom` -> `room`
        all_rooms = [link.room for link in booking.booking_rooms]
    
    room_ids = [room.id for room in all_rooms if room]
    
    if not all_rooms:
         raise HTTPException(status_code=404, detail="Booking found, but no rooms are linked to it.")

    # 4. Calculate total charges across ALL rooms
    charges = BillBreakdown()
    
    # Calculate effective checkout date:
    # If actual checkout date (today) > booking.check_out (late checkout): use today
    # If actual checkout date (today) < booking.check_out (early checkout): use booking.check_out
    today = date.today()
    effective_checkout_date = max(today, booking.check_out)
    stay_days = max(1, (effective_checkout_date - booking.check_in).days)

    if is_package:
        # Check if this is a whole_property package
        package = booking.package if booking.package else None
        is_whole_property = False
        if package:
            # Check booking_type field
            booking_type = getattr(package, 'booking_type', None)
            if booking_type:
                is_whole_property = booking_type.lower() in ['whole_property', 'whole property']
            else:
                # Fallback: if no room_types specified, treat as whole_property (legacy packages)
                room_types = getattr(package, 'room_types', None)
                is_whole_property = not room_types or not room_types.strip()
        
        package_price = package.price if package else 0
        
        if is_whole_property:
            # For whole_property packages: package price is the total amount (not multiplied by rooms/days)
            charges.package_charges = package_price
            charges.room_charges = 0  # Room charges are included in the package price
        else:
            # For room_type packages: package price is per room, per night
            num_rooms_in_package = len(all_rooms)
            charges.package_charges = package_price * num_rooms_in_package * stay_days
            charges.room_charges = 0  # Room charges are included in the package price
    else:
        charges.package_charges = 0
        # For regular bookings: calculate total room charges from ALL rooms using dynamic pricing
        total_room_cost = 0.0
        for room in all_rooms:
            dynamic_rate = calculate_dynamic_booking_price(db, room.room_type_id, booking.check_in, effective_checkout_date, room_count=1)
            total_room_cost += dynamic_rate or ((room.price or 0) * stay_days)
            
        charges.room_charges = total_room_cost
    
    # Determine start time for billing to include orders created before formal check-in
    # 1. Start with booking check-in date at 00:00:00
    check_in_datetime = datetime.combine(booking.check_in, datetime.min.time())
    
    # 2. Find the most recent checkout for ANY of the rooms to ensure we don't overlap with previous guest
    # This is a bit complex for multiple rooms, but we can take the latest checkout timestamp across all rooms
    # excluding the current booking.
    
    # Get room numbers
    room_numbers = [r.number for r in all_rooms]
    
    last_checkout_query = db.query(Checkout).filter(Checkout.room_number.in_(room_numbers))
    
    if is_package:
        last_checkout_query = last_checkout_query.filter(Checkout.package_booking_id != booking.id)
    else:
        last_checkout_query = last_checkout_query.filter(Checkout.booking_id != booking.id)
        
    last_checkout = last_checkout_query.order_by(Checkout.checkout_date.desc()).first()
    
    # Relax start time slightly to catch orders made at/before formal check-in on the first day
    check_in_datetime = check_in_datetime - timedelta(hours=1)
    
    print(f"[DEBUG] Using billing start time (relaxed): {check_in_datetime}")

    # Sum up additional food and service charges from all rooms
    # Scope to the CURRENT booking only to avoid cross-booking pollution.
    # Include orders explicitly linked to this booking, OR orders with no booking link
    # (legacy/walk-in orders) that were created during the current stay period.
    if is_package:
        # Prioritize package_booking_id across ALL rooms
        all_food_order_items = (db.query(FoodOrderItem)
                               .join(FoodOrder)
                               .options(joinedload(FoodOrderItem.food_item), joinedload(FoodOrderItem.order))
                               .filter(
                                   or_(
                                       FoodOrder.package_booking_id == booking.id,
                                       and_(
                                           FoodOrder.room_id.in_(room_ids),
                                           FoodOrder.package_booking_id == None,
                                           FoodOrder.booking_id == None,
                                           FoodOrder.created_at >= check_in_datetime
                                       )
                                   )
                               )
                               .all())
    else:
        all_food_order_items = (db.query(FoodOrderItem)
                               .join(FoodOrder)
                               .options(joinedload(FoodOrderItem.food_item), joinedload(FoodOrderItem.order))
                               .filter(
                                   FoodOrder.room_id.in_(room_ids),
                                   or_(
                                       FoodOrder.booking_id == booking.id,
                                       and_(
                                           FoodOrder.booking_id == None,
                                           FoodOrder.package_booking_id == None,
                                           FoodOrder.created_at >= check_in_datetime
                                       )
                                   )
                               )
                               .all())

    # Separate billed and unbilled items
    # Unbilled: billing_status is None, "unbilled", "unpaid" (add to bill)
    # Paid: billing_status is "paid" (show as paid, don't add to bill)
    # Billed: billing_status is "billed" (already billed, show as paid)
    unbilled_food_order_items = [item for item in all_food_order_items 
                                 if not item.order or item.order.billing_status in ["unbilled", "unpaid"] or item.order.billing_status is None]
    paid_food_order_items = [item for item in all_food_order_items 
                            if item.order and item.order.billing_status == "paid"]
    billed_food_order_items = [item for item in all_food_order_items 
                               if item.order and item.order.billing_status == "billed"]

    # Use booking's actual check_in/check_out dates for filtering unlinked services
    booking_check_in_datetime = datetime.combine(booking.check_in, datetime.min.time())
    booking_check_out_datetime = datetime.combine(booking.check_out, datetime.max.time())

    # Get ALL assigned services for these rooms (both billed and unbilled)
    # Filter by booking ID to include all services linked to this booking,
    # OR include services with no booking link but assigned during this booking's stay
    if is_package:
        # Include ALL services for this package across ALL rooms
        all_assigned_services = db.query(AssignedService).options(joinedload(AssignedService.service)).filter(
            or_(
                AssignedService.package_booking_id == booking.id,
                and_(
                    AssignedService.room_id.in_(room_ids),
                    AssignedService.package_booking_id == None,
                    AssignedService.booking_id == None,
                    AssignedService.assigned_at >= booking_check_in_datetime,
                    AssignedService.assigned_at <= booking_check_out_datetime
                )
            )
        ).all()
    else:
        all_assigned_services = db.query(AssignedService).options(joinedload(AssignedService.service)).filter(
            AssignedService.room_id.in_(room_ids)
        ).filter(
            or_(
                AssignedService.booking_id == booking.id,
                and_(
                    AssignedService.booking_id == None,
                    AssignedService.package_booking_id == None,
                    AssignedService.assigned_at >= booking_check_in_datetime,
                    AssignedService.assigned_at <= booking_check_out_datetime
                )
            )
        ).all()
    
    # Separate unbilled, paid-at-counter, and billed services
    unbilled_services = [ass for ass in all_assigned_services if ass.billing_status in ["unbilled", "unpaid"] or ass.billing_status is None]
    paid_services = [ass for ass in all_assigned_services if ass.billing_status == "paid"]
    billed_services = [ass for ass in all_assigned_services if ass.billing_status == "billed"]

    # Calculate total food charges from the individual items (only unbilled items)
    charges.food_charges = sum(
        (item.quantity * item.food_item.price) 
        if (item.food_item and (not item.order or (item.order.amount or 0) > 0)) else 0 
        for item in unbilled_food_order_items
    )
    charges.service_charges = sum(ass.override_charges if ass.override_charges is not None else ass.service.charges for ass in unbilled_services)

    # Populate detailed item lists for the bill summary - include ALL items
    charges.food_items = []
    # Add unbilled items with their actual amounts
    for item in unbilled_food_order_items:
        if item.food_item:
            # Check if order is complimentary (amount is 0)
            is_complimentary = item.order and item.order.amount == 0
            
            # HIDE complimentary items for package bookings to keep bill guest-friendly
            if is_package and is_complimentary:
                continue
                
            item_amount = 0.0 if is_complimentary else (item.quantity * item.food_item.price)
            
            charges.food_items.append({
                "item_name": item.food_item.name, 
                "quantity": item.quantity, 
                "amount": item_amount,
                "is_paid": False,
                "payment_status": "Complimentary" if is_complimentary else "Unpaid"
            })
    # Add paid items (paid at delivery) with payment details
    for item in paid_food_order_items:
        if item.food_item and item.order:
            charges.food_items.append({
                "item_name": item.food_item.name, 
                "quantity": item.quantity, 
                "amount": 0.0,  # Don't add to bill
                "is_paid": True,
                "payment_status": f"PAID ({item.order.payment_method or 'cash'})",
                "payment_method": item.order.payment_method,
                "payment_time": item.order.payment_time.isoformat() if item.order.payment_time else None,
                "gst_amount": item.order.gst_amount,
                "total_with_gst": item.order.total_with_gst
            })

    # Add billed items with zero amount
    for item in billed_food_order_items:
        if item.food_item:
            charges.food_items.append({
                "item_name": item.food_item.name, 
                "quantity": item.quantity, 
                "amount": 0.0,
                "is_paid": True
            })
    
    # Include ALL service items with payment status
    charges.service_items = []
    
    # Add unbilled services with their actual charges
    for ass in unbilled_services:
        charges.service_items.append({
            "service_name": ass.service.name, 
            "charges": ass.override_charges if ass.override_charges is not None else ass.service.charges,
            "is_paid": False,
            "payment_status": "Unpaid"
        })
    
    # Add paid-at-counter services
    for ass in paid_services:
        charges.service_items.append({
            "service_name": ass.service.name,
            "charges": 0.0,
            "is_paid": True,
            "payment_status": "PAID (at counter)"
        })
    
    for ass in billed_services:
        charges.service_items.append({
            "service_name": ass.service.name,
            "charges": 0.0,
            "is_paid": True,
            "payment_status": "Previously Billed"
        })

    # Calculate Consumables and Inventory Charges from CheckoutRequests
    import re
    from app.models.inventory import InventoryItem, StockIssue, StockIssueDetail
    
    # 1. PRE-SCAN STOCK ISSUES for Rental Prices and Asset Status across ALL rooms
    rental_map = {} # item_id -> {rental_price: float, is_payable: bool, is_fixed: bool}
    room_issues = (db.query(StockIssueDetail)
                   .join(StockIssue)
                   .filter(StockIssue.destination_location_id.in_(
                       db.query(Room.inventory_location_id).filter(Room.id.in_(room_ids))
                   ))
                   .all())
    for d in room_issues:
        iid = int(d.item_id)
        if iid not in rental_map:
            rental_map[iid] = {
                "rental_price": float(d.rental_price or 0.0),
                "is_payable": getattr(d, 'is_payable', False),
                "is_asset": d.item.is_asset_fixed if d.item else False
            }
        else:
            if float(d.rental_price or 0.0) > 0:
                rental_map[iid]["rental_price"] = max(rental_map[iid]["rental_price"], float(d.rental_price or 0.0))


    # FIX: Calculate stay_days at the top level of entire booking
    stay_days = 1
    if booking:
        checkout_date_val = booking.check_out
        checkin_date_val = booking.check_in
        if isinstance(checkout_date_val, datetime): checkout_date_val = checkout_date_val.date()
        if isinstance(checkin_date_val, datetime): checkin_date_val = checkin_date_val.date()
        stay_days = max(1, (checkout_date_val - checkin_date_val).days)

    checkout_requests = []

    if is_package:
        checkout_requests = db.query(CheckoutRequestModel).filter(
            CheckoutRequestModel.package_booking_id == booking.id,
            CheckoutRequestModel.status == "completed"
        ).all()
    else:
        checkout_requests = db.query(CheckoutRequestModel).filter(
            CheckoutRequestModel.booking_id == booking.id,
            CheckoutRequestModel.status == "completed"
        ).all()
        
    processed_ids = set() # (room_number, item_id)
    room_processed_ids = set() 
    seen_item_keys = set() # (room_number, cleaned_name)
    
    for checkout_request in checkout_requests:
        r_num = checkout_request.room_number
        if not checkout_request.inventory_data:
            continue
            
        # Aggregate within this room's request
        aggregated_room_audit = {} # item_id -> data
        generic_assets = []
        
        for item_data in checkout_request.inventory_data:
            iid = int(item_data.get('item_id') or 0)
            if not iid:
                generic_assets.append(item_data)
                continue
            
            is_rent = item_data.get('is_rentable', False)
            audit_key = (iid, is_rent)
            
            if audit_key not in aggregated_room_audit:
                aggregated_room_audit[audit_key] = {
                    "item_id": iid,
                    "is_rentable": is_rent,
                    "is_fixed_asset": False,
                    "used_qty": 0.0,
                    "damage_qty": 0.0,
                    "missing_qty": 0.0,
                    "allocated_stock": 0.0,
                    "provided_bad_charge": 0.0
                }
            
            # OR logic for fixed flag within the (iid, is_rent) group
            if item_data.get('is_fixed_asset'): aggregated_room_audit[audit_key]["is_fixed_asset"] = True
            
            aggregated_room_audit[audit_key]["used_qty"] += float(item_data.get('used_qty') or 0)
            aggregated_room_audit[audit_key]["damage_qty"] += float(item_data.get('damage_qty') or 0)
            aggregated_room_audit[audit_key]["missing_qty"] += float(item_data.get('missing_qty') or 0)
            aggregated_room_audit[audit_key]["provided_bad_charge"] += float(item_data.get('damage_charge') or item_data.get('missing_item_charge') or item_data.get('total_charge') or 0)
            aggregated_room_audit[audit_key]["allocated_stock"] += float(item_data.get('allocated_stock') or 0)

        # Process Aggregated Room Audit
        for (item_id, is_rent), item_data in aggregated_room_audit.items():
            used_qty = item_data['used_qty']
            damage_qty = item_data['damage_qty']
            missing_qty = item_data['missing_qty']
            allocated_stock = item_data['allocated_stock']
            
            # Use explicit rentable flag from aggregated data
            is_rentable_audit = is_rent
            is_fixed_audit = item_data['is_fixed_asset']
            
            # Fetch Latest Master Info
            inv_item = db.query(InventoryItem).options(joinedload(InventoryItem.category)).filter(InventoryItem.id == item_id).first()
            if not inv_item: continue

            room_processed_ids.add((r_num, item_id))
            # processed_ids.add(item_id) # For global tracking if needed - removed as it was causing issues
            
            clean_name = re.sub(r'\s*\(\s*[xX]\d+[^)]*\)', '', inv_item.name).strip()
            item_key = f"{clean_name.lower()}_{item_id}"
            if (r_num, item_key) in seen_item_keys: continue
            seen_item_keys.add((r_num, item_key))
            
            # Consumables Pricing Fix: Prioritize selling_price (guest price) over unit_price (purchase price/cost)
            selling_price_base = float(inv_item.selling_price or 0.0)
            cost_price_with_gst = float(inv_item.unit_price or 0.0) * (1.0 + float(inv_item.gst_rate or 0.0) / 100.0)
            
            # Priority: 1. Selling Price, 2. Cost Price + GST
            replacement_price = selling_price_base if selling_price_base > 0 else (cost_price_with_gst if cost_price_with_gst > 0 else 0.0)
            
            # Safety fallback for tax-exclusive prices if everything is still zero
            if replacement_price == 0 and selling_price_base > 0:
                 replacement_price = selling_price_base * 1.12
            elif replacement_price == 0 and cost_price_with_gst > 0:
                 replacement_price = cost_price_with_gst
            
            # Classification from Audit
            is_rentable_audit = item_data.get('is_rentable', False)
            is_fixed_audit = item_data.get('is_fixed_asset', False)
            clean_name = re.sub(r'\s*\(\s*[xX]\d+[^)]*\)', '', inv_item.name).strip()
            item_key = f"{clean_name.lower()}_{item_id}"
            
            # Classification logic synced
            is_amenity = any(kw in clean_name.lower() for kw in ["water", "soap", "shampoo", "toothpaste", "vanity"])
            asset_keywords = ["linen", "electronic", "furniture", "asset", "fixed", "appliance", "electrical", "fixture", "towel", "bedsheet"]
            is_asset_category = any(kw in (inv_item.category.name if inv_item.category else "").lower() for kw in asset_keywords)
            
            consumable_keywords = ["food", "drink", "beverage", "amenity", "toiletries", "mini bar", "consumable", "provision"]
            is_consumable_category = any(kw in (inv_item.category.name if inv_item.category else "").lower() for kw in consumable_keywords) or is_amenity

            is_rentable = is_rentable_audit or "rental" in (inv_item.category.name if inv_item.category else "").lower()
            if is_asset_category and not ("rental" in (inv_item.category.name if inv_item.category else "").lower() or is_rentable_audit):
                is_rentable = False
                
            if is_consumable_category:
                is_rentable = False
                
            is_fixed_asset = is_fixed_audit or inv_item.is_asset_fixed or is_asset_category
            
            # Display logic synced
            display_key = f"{r_num}_{item_key}_{is_rentable_audit}"
            if display_key in seen_item_keys: continue
            seen_item_keys.add(display_key)
            
            # Support Section 5 fallback detection
            seen_item_keys.add(f"{r_num}_{item_key}")
            seen_item_keys.add(item_key)
            
            # 2. Calculate Rental/Usage Charge
            usage_charge = 0.0
            rm = rental_map.get(item_id, {})
            rental_unit_price = rm.get("rental_price", 0) or ((inv_item.selling_price or inv_item.unit_price or 0.0) if is_rentable else 0)
            
            if used_qty > 0 or allocated_stock > 0:
                limit = inv_item.complimentary_limit or 0
                if is_rentable:
                    # Apply rent to all audited units, even if damaged or lost.
                    total_audited_qty = max(used_qty, allocated_stock)
                    
                    # Bypass master-data limit for explicit rentals from audit
                    audit_limit = float(item_data.get('complimentary_qty') or item_data.get('complimentary_limit') or 0.0)
                    actual_limit = audit_limit if audit_limit > 0 else 0.0
                    
                    payable_qty = max(0, total_audited_qty - actual_limit)
                    
                    # FIX: Calculate actual rental sum for this room/item to avoid doubling
                    try:
                        current_room_obj = db.query(Room).filter(Room.number == r_num).first()
                        if current_room_obj and current_room_obj.inventory_location_id:
                             actual_rental_sum = db.query(func.sum(StockIssueDetail.issued_quantity * StockIssueDetail.rental_price)).join(StockIssue).filter(
                                StockIssue.destination_location_id == current_room_obj.inventory_location_id,
                                StockIssueDetail.item_id == item_id,
                                StockIssueDetail.rental_price > 0,
                                StockIssue.issue_date >= (getattr(booking, 'checked_in_at', None) or booking.check_in)
                            ).scalar() or 0.0
                             if actual_rental_sum > 0:
                                usage_charge = float(actual_rental_sum) * stay_days
                             else:
                                usage_charge = payable_qty * rental_unit_price * stay_days
                        else:
                            usage_charge = payable_qty * rental_unit_price * stay_days
                    except:
                         usage_charge = payable_qty * rental_unit_price * stay_days
                
                # Consumables Fix: If it's an amenity or marked sellable, treat as consumable
                elif is_amenity or (getattr(inv_item, 'is_sellable_to_guest', False) or limit > 0):
                    # Use central helper for consistent calculation
                    u_charge, rep_price, chargeable_qty = calculate_consumable_charge(inv_item, used_qty, limit_from_audit=limit)
                    usage_charge = u_charge
                    replacement_price = rep_price


            # 3. Calculate Damage/Missing Charge
            calc_bad_charge = (damage_qty + missing_qty) * replacement_price
            bad_charge = max(calc_bad_charge, float(item_data.get('provided_bad_charge') or 0))

            if is_rentable:
                display_qty = max(used_qty, allocated_stock)
                
                item_notes = f"Room {r_num} Audit"
                if (damage_qty + missing_qty) > 0 and usage_charge == 0:
                    item_notes += " - Rent waived (Damaged/Missing)"

                charges.inventory_usage.append({
                    "date": checkout_request.completed_at or datetime.now(),
                    "room_number": r_num,
                    "item_name": f"Room {r_num}: {clean_name}",
                    "category": inv_item.category.name if inv_item.category else "Rental",
                    "quantity": display_qty,
                    "unit": inv_item.unit or "pcs",
                    "rental_price": rental_unit_price,
                    "rental_charge": usage_charge,
                    "is_rental": True,
                    "is_payable": (usage_charge > 0 or (damage_qty + missing_qty) > 0),
                    "notes": item_notes
                })
                if usage_charge > 0:
                    charges.inventory_charges = (charges.inventory_charges or 0) + usage_charge
            
            # CHANGE: Changed from 'elif' to 'if' for multiple room checkout too
            if is_fixed_asset:
                if (damage_qty + missing_qty) > 0:
                    charges.fixed_assets.append({
                        "item_name": f"Room {r_num}: {clean_name}",
                        "status": "Damaged/Missing",
                        "quantity": damage_qty + missing_qty,
                        "notes": f"Room {r_num} Audit"
                    })
                
                if bad_charge > 0:
                    charges.asset_damage_charges = (charges.asset_damage_charges or 0) + bad_charge
                    label_suffix = " (Damaged)" if damage_qty > 0 else " (Missing)"
                    if damage_qty > 0 and missing_qty > 0: label_suffix = " (Damaged/Missing)"
                    charges.asset_damages.append({
                        "item_name": f"Room {r_num}: {clean_name}{label_suffix}",
                        "replacement_cost": bad_charge,
                        "notes": f"Room {r_num} - Damaged: {damage_qty}, Missing: {missing_qty}"
                    })
            else:
                # Consumables
                total_qty = used_qty 
                total_item_charge = usage_charge + bad_charge
                if total_qty > 0 or total_item_charge > 0:
                    label = f"Room {r_num}: {clean_name}"
                    if total_qty > 1: label += f" (x{int(total_qty)})"
                    
                    if damage_qty > 0:
                        label += f" ({int(damage_qty)} Damaged)"
                    
                    charges.consumables_charges = (charges.consumables_charges or 0) + total_item_charge
                    charges.consumables_items.append({
                        "date": checkout_request.completed_at or datetime.now(),
                        "item_id": item_id,
                        "item_name": label,
                        "actual_consumed": total_qty,
                        "complimentary_limit": inv_item.complimentary_limit or 0,
                        "charge_per_unit": total_item_charge / total_qty if total_qty > 0 else replacement_price,
                        "total_charge": total_item_charge
                    })

        # Process Generic Assets (No item_id)
        for asset_data in generic_assets:
            replacement_cost = float(asset_data.get('replacement_cost', 0))
            if replacement_cost > 0:
                item_name = asset_data.get('item_name', 'Damaged Asset')
                charges.asset_damage_charges = (charges.asset_damage_charges or 0) + replacement_cost
                charges.asset_damages.append({
                    "item_name": f"Room {r_num}: {item_name} (Damaged)",
                    "replacement_cost": replacement_cost,
                    "notes": asset_data.get('notes', 'Asset damage')
                })

    # 5. Stock Issues NOT in Audit (Across all rooms)
    stock_issues = (db.query(StockIssue)
                    .options(joinedload(StockIssue.details).joinedload(StockIssueDetail.item))
                    .filter(StockIssue.destination_location_id.in_(
                        db.query(Room.inventory_location_id).filter(Room.id.in_(room_ids))
                    ),
                    StockIssue.issue_date >= check_in_datetime - timedelta(hours=24))
                    .all())
    
    for issue in stock_issues:
        r_num = next((r.number for r in all_rooms if r.inventory_location_id == issue.destination_location_id), "Unknown")
        for detail in issue.details:
            if not detail.item: continue
            clean_name = re.sub(r'\s*\(\s*[xX]\d+[^)]*\)', '', detail.item.name).strip()
            item_key = f"{clean_name.lower()}_{detail.item_id}"
            
            # Check per-room tracking
            if ((r_num, int(detail.item_id)) in room_processed_ids) or ((r_num, item_key) in seen_item_keys):
                continue
            
            room_processed_ids.add((r_num, int(detail.item_id)))
            seen_item_keys.add((r_num, item_key))
            
            r_price = float(detail.rental_price or 0.0)
            u_charge = 0.0
            if r_price > 0:
                u_charge = r_price * detail.issued_quantity
            elif getattr(detail, 'is_payable', False):
                p = float(detail.item.selling_price or detail.item.unit_price or 0.0)
                u_charge = p * detail.issued_quantity

            # Check for manual damage
            bad_charge = 0.0
            if getattr(detail, 'is_damaged', False):
                s_price = float(detail.item.selling_price or 0.0)
                rep_price = s_price if s_price > 0 else (float(detail.item.unit_price or 0.0) * (1.0 + float(detail.item.gst_rate or 0.0) / 100.0))
                bad_charge = detail.issued_quantity * rep_price

            is_rentable = r_price > 0
            is_fixed_asset = detail.item.is_asset_fixed if detail.item else False

            if is_rentable:
                charges.inventory_usage.append({
                    "date": issue.issue_date,
                    "item_name": f"Room {r_num}: {clean_name}",
                    "room_number": r_num,
                    "category": detail.item.category.name if detail.item.category else "Rental",
                    "quantity": detail.issued_quantity,
                    "unit": detail.unit or "pcs",
                    "rental_price": r_price,
                    "rental_charge": u_charge,
                    "is_rental": True,
                    "is_payable": u_charge > 0,
                    "notes": "Issued stock (unverified)"
                })
                if u_charge > 0:
                    charges.inventory_charges = (charges.inventory_charges or 0) + u_charge
            elif is_fixed_asset:
                if bad_charge > 0:
                    charges.fixed_assets.append({
                        "item_name": f"Room {r_num}: {clean_name}",
                        "status": "Damaged",
                        "quantity": detail.issued_quantity,
                        "notes": "Issued stock (pre-marked)"
                    })
            
            if bad_charge > 0:
                charges.asset_damage_charges = (charges.asset_damage_charges or 0) + bad_charge
                charges.asset_damages.append({
                    "item_name": f"Room {r_num}: {clean_name} (Damaged)",
                    "replacement_cost": bad_charge,
                    "notes": f"Room {r_num} - Damaged stock issue"
                })


    # Summary
    total_missing_charges = charges.asset_damage_charges or 0
    total_consumables_charges = charges.consumables_charges or 0
    total_inventory_charges = charges.inventory_charges or 0

    # Calculate GST
    # Room charges: 5% GST if < 5000, 12% GST if 5000-7500, 18% GST if > 7500
    # FIX: Calculate GST for each room individually based on its nightly rate
    charges.room_gst = 0.0
    if not is_package:
        for room in all_rooms:
            room_price = room.price or 0
            room_gst_rate = 0.18
            if room_price < 5000:
                room_gst_rate = 0.05
            elif room_price <= 7500:
                room_gst_rate = 0.12
            
            # Calculate total charge for this room
            room_total = room_price * stay_days
            charges.room_gst += room_total * room_gst_rate
    
    # Package charges: Same rule as room charges
    # Determine daily rate for package to find the slab
    package_daily_rate = 0
    if is_package:
        if is_whole_property:
            package_daily_rate = (package.price if package else 0) / max(1, stay_days)
        else:
            package_daily_rate = package.price if package else 0
            
    package_gst_rate = 0.18
    if package_daily_rate > 0:
        if package_daily_rate < 5000:
            package_gst_rate = 0.05
        elif package_daily_rate <= 7500:
            package_gst_rate = 0.12
            
    charges.package_gst = (charges.package_charges or 0) * package_gst_rate
    
    # Food charges: 5% GST always
    food_charge_amount = charges.food_charges or 0
    if food_charge_amount > 0:
        charges.food_gst = food_charge_amount * 0.05
        
    # Service GST: Calculate based on individual service rates
    charges.service_gst = 0.0
    for ass in unbilled_services:
        gst_rate = 0.05 # Fixed 5% for all services as per new rule
        amount = ass.override_charges if ass.override_charges is not None else ass.service.charges
        charges.service_gst += amount * gst_rate
        
    # Consumables GST: 5%
    if charges.consumables_charges and charges.consumables_charges > 0:
        charges.consumables_gst = charges.consumables_charges * 0.05
    
    # Inventory GST: 18% (default for most inventory items)
    if charges.inventory_charges and charges.inventory_charges > 0:
        charges.inventory_gst = charges.inventory_charges * 0.05

    # Asset Damage GST: 0% (Removed as per request)
    if charges.asset_damage_charges and charges.asset_damage_charges > 0:
        charges.asset_damage_gst = 0.0
    
    # Total GST
    charges.total_gst = (charges.room_gst or 0) + (charges.food_gst or 0) + (charges.service_gst or 0) + (charges.package_gst or 0) + (charges.consumables_gst or 0) + (charges.inventory_gst or 0) + (charges.asset_damage_gst or 0)
    
    # Total due (subtotal before GST)
    charges.total_due = sum([
        charges.room_charges or 0, 
        charges.food_charges or 0, 
        charges.service_charges or 0, 
        charges.package_charges or 0,
        charges.consumables_charges or 0,
        charges.inventory_charges or 0,
        charges.asset_damage_charges or 0
    ])
    
    # Add advance deposit info to charges
    charges.advance_deposit = getattr(booking, 'advance_deposit', 0.0) or 0.0

    # Assume number_of_guests is a field on the booking model. Default to 1 if not present.
    number_of_guests = getattr(booking, 'number_of_guests', 1)

    return {
        "booking": booking, "all_rooms": all_rooms, "charges": charges, 
        "is_package": is_package, "stay_nights": stay_days, "number_of_guests": number_of_guests,
        "effective_checkout_date": effective_checkout_date
    }


@router.get("/{room_number}", response_model=BillSummary)
def get_bill_for_booking(room_number: str, checkout_mode: str = "multiple", db: Session = Depends(get_db), current_user: User = Depends(get_current_user), branch_id: int = Depends(get_branch_id)):
    """
    Returns a bill summary for the booking associated with the given room number.
    If checkout_mode is 'single', calculates bill for that room only.
    If checkout_mode is 'multiple', calculates bill for all rooms in the booking.
    """
    if checkout_mode == "single":
        bill_data = _calculate_bill_for_single_room(db, room_number, branch_id)
        effective_checkout = bill_data.get("effective_checkout_date", bill_data["booking"].check_out)
        return BillSummary(
            guest_name=bill_data["booking"].guest_name,
            room_numbers=[bill_data["room"].number],
            number_of_guests=bill_data["number_of_guests"],
            stay_nights=bill_data["stay_nights"],
            check_in=bill_data["booking"].check_in,
            check_out=effective_checkout,  # Use effective checkout date (today if late, booking.check_out if early)
            charges=bill_data["charges"]
        )
    else:
        bill_data = _calculate_bill_for_entire_booking(db, room_number, branch_id)
        effective_checkout = bill_data.get("effective_checkout_date", bill_data["booking"].check_out)
        return BillSummary(
            guest_name=bill_data["booking"].guest_name,
            room_numbers=sorted([room.number for room in bill_data["all_rooms"]]),
            number_of_guests=bill_data["number_of_guests"],
            stay_nights=bill_data["stay_nights"],
            check_in=bill_data["booking"].check_in,
            check_out=effective_checkout,  # Use effective checkout date (today if late, booking.check_out if early)
            charges=bill_data["charges"]
        )


@router.post("/checkout/{room_number}", response_model=CheckoutSuccess)
def process_booking_checkout(room_number: str, request: CheckoutRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user), branch_id: int = Depends(get_branch_id)):
    """
    Finalizes the checkout for a room or entire booking.
    If checkout_mode is 'single', only the specified room is checked out.
    If checkout_mode is 'multiple', all rooms in the booking are checked out together.
    """
    checkout_mode = request.checkout_mode or "multiple"
    
    # Ensure checkout_mode is valid
    if checkout_mode not in ["single", "multiple"]:
        checkout_mode = "multiple"  # Default to multiple if invalid
    
    # Check if checkout request exists and inventory is verified
    room = db.query(Room).filter(Room.number == room_number, Room.branch_id == branch_id).first()
    if room:
        # Find active booking
        booking_link = (db.query(BookingRoom)
                        .join(Booking)
                        .filter(BookingRoom.room_id == room.id, Booking.status.in_(['checked-in', 'checked_in', 'booked']))
                        .order_by(Booking.id.desc()).first())
        
        package_link = None
        booking = None
        is_package = False
        
        if booking_link:
            booking = booking_link.booking
        else:
            package_link = (db.query(PackageBookingRoom)
                            .join(PackageBooking)
                            .filter(PackageBookingRoom.room_id == room.id, PackageBooking.status.in_(['checked-in', 'checked_in', 'booked']))
                            .order_by(PackageBooking.id.desc()).first())
            if package_link:
                booking = package_link.package_booking
                is_package = True
        
        if booking:
            # Check for checkout request based on checkout mode
            pending_requests = []
            
            if checkout_mode == "single":
                # For single room checkout, just check this room
                request_query = db.query(CheckoutRequestModel).filter(
                    CheckoutRequestModel.room_number == room.number,
                    CheckoutRequestModel.status.in_(["pending"])
                )
                if is_package:
                    request_query = request_query.filter(CheckoutRequestModel.package_booking_id == booking.id)
                else:
                    request_query = request_query.filter(CheckoutRequestModel.booking_id == booking.id)
                    
                pending_req = request_query.order_by(CheckoutRequestModel.id.desc()).first()
                if pending_req and not pending_req.inventory_checked:
                    pending_requests.append(pending_req)
            else:
                # For multiple room checkout, check all rooms in the booking
                request_query = db.query(CheckoutRequestModel).filter(
                    CheckoutRequestModel.status.in_(["pending"])
                )
                if is_package:
                    request_query = request_query.filter(CheckoutRequestModel.package_booking_id == booking.id)
                else:
                    request_query = request_query.filter(CheckoutRequestModel.booking_id == booking.id)
                    
                unverified_reqs = request_query.all()
                for req in unverified_reqs:
                    if not req.inventory_checked:
                        pending_requests.append(req)
            
            # Block checkout if any relevant inventory is not checked
            if pending_requests:
                unverified_rooms = ", ".join([r.room_number for r in pending_requests])
                raise HTTPException(
                    status_code=400, 
                    detail=f"Inventory must be checked before completing checkout. Please verify inventory for room(s): {unverified_rooms}"
                )
    
    if checkout_mode == "single":
        # Single room checkout
        # Calculate bill first - this will validate that there's an active booking
        bill_data = _calculate_bill_for_single_room(db, room_number, branch_id)
        booking = bill_data["booking"]
        room = bill_data["room"]
        charges = bill_data["charges"]
        is_package = bill_data["is_package"]
        
        # Validate booking is in a valid state (this is the source of truth, not room status)
        if booking.status not in ['checked-in', 'checked_in', 'booked', 'checked-out', 'checked_out', 'checked out']:
            raise HTTPException(status_code=400, detail=f"Booking cannot be checked out. Current status: {booking.status}")
        
        # PRE-CHECKOUT CLEANUP: Check for and delete any orphaned checkouts BEFORE attempting checkout
        # This prevents unique constraint violations
        today = date.today()
        existing_room_checkout = db.query(Checkout).filter(
            Checkout.room_number == room_number,
            func.date(Checkout.checkout_date) == today
        ).first()
        
        # Also check for any checkout for this booking (not just today)
        existing_booking_checkout = None
        if not is_package:
            existing_booking_checkout = db.query(Checkout).filter(
                Checkout.booking_id == booking.id
            ).first()
        else:
            existing_booking_checkout = db.query(Checkout).filter(
                Checkout.package_booking_id == booking.id
            ).first()
        
        # If checkout exists, verify the room status matches
        if existing_room_checkout or existing_booking_checkout:
            # Use the most recent checkout
            checkout_to_check = existing_room_checkout or existing_booking_checkout
            
            # If room is still not "Available", the checkout didn't complete properly - delete and allow retry
            if room.status != "Available":
                # Delete the orphaned checkout record(s) and allow retry
                print(f"[CLEANUP] Found orphaned checkout(s) for room {room_number}, booking {booking.id}. Cleaning up...")
                try:
                    deleted_count = 0
                    if existing_room_checkout:
                        # Unlink checkout requests first to avoid FK constraints
                        db.query(CheckoutRequestModel).filter(CheckoutRequestModel.checkout_id == existing_room_checkout.id).update({"checkout_id": None})
                        db.delete(existing_room_checkout)
                        deleted_count += 1
                        print(f"[CLEANUP] Deleted orphaned room checkout record {existing_room_checkout.id}")
                    if existing_booking_checkout and existing_booking_checkout.id != (existing_room_checkout.id if existing_room_checkout else None):
                        # Unlink checkout requests first
                        db.query(CheckoutRequestModel).filter(CheckoutRequestModel.checkout_id == existing_booking_checkout.id).update({"checkout_id": None})
                        db.delete(existing_booking_checkout)
                        deleted_count += 1
                        print(f"[CLEANUP] Deleted orphaned booking checkout record {existing_booking_checkout.id}")
                    db.commit()
                    print(f"[CLEANUP] Successfully deleted {deleted_count} orphaned checkout record(s). Proceeding with new checkout.")
                    # Continue to create new checkout - don't return error
                except Exception as del_error:
                    print(f"[ERROR] Failed to delete orphaned checkout: {str(del_error)}")
                    db.rollback()
                    # Still try to proceed - maybe the checkout will work
            else:
                # Room is already checked out - return existing checkout info instead of error
                print(f"[INFO] Valid checkout already exists for room {room_number} (ID: {checkout_to_check.id})")
                return CheckoutSuccess(
                    checkout_id=checkout_to_check.id,
                    grand_total=checkout_to_check.grand_total,
                    checkout_date=checkout_to_check.checkout_date or checkout_to_check.created_at
                )
        
        # Check if room is already available (already checked out)
        if room.status == "Available":
            # Try to find the existing checkout
            existing = db.query(Checkout).filter(
                Checkout.room_number == room_number,
                Checkout.branch_id == branch_id
            ).order_by(Checkout.created_at.desc()).first()
            if existing:
                return CheckoutSuccess(
                    checkout_id=existing.id,
                    grand_total=existing.grand_total,
                    checkout_date=existing.checkout_date or existing.created_at
                )
            raise HTTPException(
                status_code=409,
                detail=f"Room {room_number} is already available (checked out). Please refresh the page to see updated status."
            )
        
        # Check if booking is already checked out (more reliable than room status)
        if booking.status in ['checked_out', 'checked-out']:
            # But verify - if room is not Available, booking status might be wrong
            if room.status != "Available":
                # Booking status is wrong - fix it
                booking.status = "checked-in"
                db.commit()
            else:
                raise HTTPException(
                    status_code=409, 
                    detail=f"Booking for room {room_number} has already been checked out. Please refresh the page to see updated status."
                )
        
        try:
            # ===== ENHANCED CHECKOUT PROCESSING =====
            
            # 1. Process Pre-Checkout Verification
            consumables_charges = 0.0
            asset_damage_charges = 0.0
            key_card_fee = 0.0
            
            if request.room_verifications:
                # Find verification for this room
                room_verification = next(
                    (rv for rv in request.room_verifications if rv.room_number == room.number),
                    None
                )
                if room_verification:
                    # Process consumables audit
                    consumables_audit = process_consumables_audit(
                        db, room.id, room_verification.consumables
                    )
                    consumables_charges = consumables_audit["total_charge"]
                    
                    # Process asset damages
                    asset_damage = process_asset_damage_check(room_verification.asset_damages)
                    asset_damage_charges = asset_damage["total_charge"]
                    
                    # Key card fee
                    if not room_verification.key_card_returned:
                        key_card_fee = 50.0  # Default lost key fee
            
            # 2. Calculate Late Checkout Fee
            actual_checkout_time = request.actual_checkout_time or datetime.now()
            late_checkout_fee = calculate_late_checkout_fee(
                booking.check_out,
                actual_checkout_time,
                room.price or 0.0
            )
            
            # 3. Get Advance Deposit
            advance_deposit = getattr(booking, 'advance_deposit', 0.0) or 0.0
            
            # 4. Calculate final bill with all charges
            # 4. Calculate final bill with all charges
            
            # Start with the DB-calculated total
            base_total = charges.total_due
            base_gst = charges.total_gst or 0
            
            # If we calculated fresh charges from verification data, use them INSTEAD of what's in DB
            if request.room_verifications:
                # Subtract DB values to avoiding double counting
                base_total -= (charges.consumables_charges or 0)
                base_total -= (charges.asset_damage_charges or 0)
                
                base_gst -= (charges.consumables_gst or 0)
                base_gst -= (charges.asset_damage_gst or 0)
            
            subtotal = base_total + consumables_charges + asset_damage_charges + key_card_fee + late_checkout_fee
            
            # Recalculate GST with new charges (consumables and asset damages may have GST)
            # For simplicity, apply same GST rate to consumables as food (5%)
            consumables_gst = consumables_charges * 0.05
            asset_damage_gst = 0.0 # No GST on asset damages as per request
            
            # Use the calculated GST from charges (already includes room, food, and package GST)
            tax_amount = base_gst + consumables_gst + asset_damage_gst
            
            discount_amount = max(0, request.discount_amount or 0)
            tips_gratuity = max(0, request.tips_gratuity or 0.0)
            
            # Grand total before advance deposit deduction
            grand_total_before_advance = max(0, subtotal + tax_amount - discount_amount + tips_gratuity)
            
            # Deduct advance deposit
            grand_total = max(0, grand_total_before_advance - advance_deposit)
            
            # 5. Get effective checkout date for billing
            effective_checkout = bill_data.get("effective_checkout_date", booking.check_out)
            effective_checkout_datetime = datetime.combine(effective_checkout, datetime.min.time())
            
            # 6. Generate invoice number (with retry logic for uniqueness)
            invoice_number = None
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    invoice_number = generate_invoice_number(db)
                    # Check if this invoice number already exists
                    existing_invoice = db.query(Checkout).filter(Checkout.invoice_number == invoice_number).first()
                    if not existing_invoice:
                        break  # Invoice number is unique, proceed
                    else:
                        print(f"[WARNING] Generated duplicate invoice number {invoice_number}, retrying... (attempt {attempt + 1}/{max_retries})")
                        if attempt == max_retries - 1:
                            # Last attempt failed, use checkout ID-based fallback
                            print(f"[WARNING] All retries failed, will use checkout ID-based invoice number")
                            invoice_number = None
                except Exception as inv_error:
                    print(f"[WARNING] Error generating invoice number: {str(inv_error)}")
                    if attempt == max_retries - 1:
                        invoice_number = None
            
            # 7. Check if there's already a checkout with this booking_id (unique constraint)
            # This MUST be checked BEFORE creating the checkout to avoid unique constraint violation
            # Also check for orphaned checkouts and clean them up
            existing_booking_checkout = None
            if not is_package:
                existing_booking_checkout = db.query(Checkout).filter(Checkout.booking_id == booking.id).first()
            else:
                existing_booking_checkout = db.query(Checkout).filter(Checkout.package_booking_id == booking.id).first()
            
            # If checkout already exists, check if it's orphaned (room still checked-in)
            if existing_booking_checkout:
                # Check room status - if room is still checked-in, this is an orphaned checkout
                if room.status != "Available":
                    print(f"[CLEANUP] Found orphaned checkout {existing_booking_checkout.id} for booking {booking.id} (room {room_number} status: {room.status}). Deleting it.")
                    try:
                        # Also delete related records first to avoid foreign key constraints
                        # Delete checkout verifications
                        db.query(CheckoutVerification).filter(CheckoutVerification.checkout_id == existing_booking_checkout.id).delete()
                        # Delete checkout payments
                        db.query(CheckoutPayment).filter(CheckoutPayment.checkout_id == existing_booking_checkout.id).delete()
                        # Unlink checkout requests
                        db.query(CheckoutRequestModel).filter(CheckoutRequestModel.checkout_id == existing_booking_checkout.id).update({"checkout_id": None})
                        # Now delete the checkout
                        db.delete(existing_booking_checkout)
                        db.commit()
                        print(f"[CLEANUP] Successfully deleted orphaned checkout {existing_booking_checkout.id} and related records")
                        # Continue to create new checkout
                        existing_booking_checkout = None
                    except Exception as del_error:
                        print(f"[ERROR] Failed to delete orphaned checkout: {str(del_error)}")
                        import traceback
                        print(traceback.format_exc())
                        db.rollback()
                        # Raise error so user knows to retry
                        raise HTTPException(
                            status_code=409,
                            detail=f"Found an orphaned checkout record but couldn't delete it. Please try again or contact support. Error: {str(del_error)}"
                        )
                else:
                    # Room is available, checkout is valid - return it
                    print(f"[INFO] Valid checkout already exists for booking {booking.id} (ID: {existing_booking_checkout.id}), returning it")
                    return CheckoutSuccess(
                        checkout_id=existing_booking_checkout.id,
                        grand_total=existing_booking_checkout.grand_total,
                        checkout_date=existing_booking_checkout.checkout_date or existing_booking_checkout.created_at
                    )
            
            booking_id_to_set = None
            package_booking_id_to_set = None
            
            if True:  # Always set booking_id since we've confirmed no existing checkout
                booking_id_to_set = booking.id if not is_package else None
                package_booking_id_to_set = booking.id if is_package else None
            
            # Create detailed bill structure for storage
            # Safely convert BillBreakdown object to dict
            from fastapi.encoders import jsonable_encoder
            charges_dict = jsonable_encoder(charges)
            
            bill_details_data = jsonable_encoder({
                "generated_at": datetime.now(),
                "charges_breakdown": charges_dict,
                "consumables_audit": {
                    "charges": consumables_charges,
                    "gst": consumables_gst,
                    "items": getattr(charges, "consumables_items", [])
                },
                "asset_damages": {
                    "charges": asset_damage_charges,
                    "gst": asset_damage_gst,
                    "items": getattr(charges, "asset_damages", [])
                },
                "inventory_usage": getattr(charges, "inventory_usage", []),
                "fixed_assets": getattr(charges, "fixed_assets", [])
            })

            # 8. Create enhanced checkout record
            new_checkout = Checkout(
                booking_id=booking_id_to_set,
                package_booking_id=package_booking_id_to_set,
                room_total=charges.room_charges,
                food_total=charges.food_charges,
                service_total=charges.service_charges,
                package_total=charges.package_charges,
                tax_amount=tax_amount,
                discount_amount=discount_amount,
                grand_total=grand_total,
                payment_method=request.payment_method or "cash",  # Default if not provided
                payment_status="Paid",
                guest_name=booking.guest_name,
                room_number=room.number,
                checkout_date=effective_checkout_datetime,
                # Enhanced fields
                late_checkout_fee=late_checkout_fee,
                consumables_charges=consumables_charges,
                inventory_charges=getattr(charges, 'inventory_charges', 0.0) or 0.0,
                asset_damage_charges=asset_damage_charges,
                key_card_fee=key_card_fee,
                advance_deposit=advance_deposit,
                tips_gratuity=tips_gratuity,
                guest_gstin=request.guest_gstin,
                is_b2b=request.is_b2b or False,
                invoice_number=invoice_number,
                bill_details=bill_details_data,  # Store the detailed bill
                branch_id=branch_id
            )
            # Add checkout to session first, then set invoice_number if needed
            db.add(new_checkout)
            db.flush()  # Flush to get checkout ID
            
            # If invoice_number wasn't generated or is duplicate, create one based on checkout ID
            if not invoice_number:
                invoice_number = f"INV-{new_checkout.id:06d}"
                new_checkout.invoice_number = invoice_number
            else:
                # Double-check invoice number is still unique (race condition protection)
                existing_invoice = db.query(Checkout).filter(
                    Checkout.invoice_number == invoice_number,
                    Checkout.id != new_checkout.id
                ).first()
                if existing_invoice:
                    print(f"[WARNING] Invoice number {invoice_number} became duplicate, using checkout ID-based number")
                    invoice_number = f"INV-{new_checkout.id:06d}"
                    new_checkout.invoice_number = invoice_number
            
            # 9. Create checkout verification records
            if request.room_verifications:
                room_verification = next(
                    (rv for rv in request.room_verifications if rv.room_number == room.number),
                    None
                )
                if room_verification:
                    create_checkout_verification(db, new_checkout.id, room_verification, room.id, branch_id=branch_id)
            else:
                # Fallback: Create verification from CheckoutRequest inventory_data
                # Fetch CheckoutRequest (similar to logic in Step 12)
                checkout_req = None
                if is_package:
                    checkout_req = db.query(CheckoutRequestModel).filter(
                        CheckoutRequestModel.package_booking_id == booking.id,
                        CheckoutRequestModel.status == "completed"
                    ).order_by(CheckoutRequestModel.id.desc()).first()
                else:
                    checkout_req = db.query(CheckoutRequestModel).filter(
                        CheckoutRequestModel.booking_id == booking.id,
                        CheckoutRequestModel.status == "completed"
                    ).order_by(CheckoutRequestModel.id.desc()).first()
                
                if checkout_req and checkout_req.inventory_data:
                    from app.schemas.checkout import RoomVerificationData, ConsumableAuditItem, AssetDamageItem
                    
                    consumables = []
                    asset_damages = []
                    
                    for item in checkout_req.inventory_data:
                        if item.get('is_fixed_asset') and not item.get('is_rentable', False):
                            # Fixed Asset (Damage)
                            if float(item.get('damage_qty', 0)) > 0 or float(item.get('missing_qty', 0)) > 0:
                                asset_damages.append(AssetDamageItem(
                                    item_name=item.get('item_name', 'Unknown Asset'),
                                    replacement_cost=float(item.get('missing_item_charge', 0) or item.get('damage_charge', 0) or item.get('total_charge', 0)),
                                    notes=item.get('notes')
                                ))
                        else:
                            # Consumable or Rentable
                            # Note: Rentables are treated as consumables for "Return" purposes in Service Request, 
                            # but we need to ensure they are captured.
                            # We create a ConsumableAuditItem with extra attributes using a dynamic class or dict approach? 
                            # Pydantic models are strict. We can subclasses or just rely on the fact create_checkout_verification iterates it.
                            # But wait, create_checkout_verification expects RoomVerificationData which expects ConsumableAuditItem.
                            
                            # We can inject 'issued_qty' and 'is_rentable' into the item object if we create a custom object
                            class ExtendedConsumableItem:
                                def __init__(self, data):
                                    self.item_id = int(data.get('item_id'))
                                    self.item_name = data.get('item_name', 'Unknown')
                                    # Used qty + Missing Qty = Actual Consumed (for consumables)
                                    # For rentables, consumed usually means missing/not returned?
                                    self.actual_consumed = float(data.get('used_qty', 0)) + float(data.get('missing_qty', 0))
                                    self.missing_qty = float(data.get('missing_qty', 0))
                                    self.complimentary_limit = int(data.get('complimentary_limit', 0))
                                    self.charge_per_unit = float(data.get('unit_price', 0))
                                    self.total_charge = float(data.get('total_charge', 0))
                                    # Extended fields
                                    self.issued_qty = float(data.get('allocated_stock', 0))
                                    self.is_rentable = data.get('is_rentable', False)
                                    
                                # Pydantic compatibility (for .item_id access)
                                def __getattr__(self, name):
                                    return self.__dict__.get(name)

                            consumables.append(ExtendedConsumableItem(item))
                            
                            # Also check for Damages to Rentables - add to asset damages too if needed?
                            # Usually rentables damage is handled in inventory_data items with damage_qty
                            if item.get('is_rentable') and float(item.get('damage_qty', 0)) > 0:
                                 asset_damages.append(AssetDamageItem(
                                    item_name=f"{item.get('item_name')} (Damage)",
                                    replacement_cost=float(item.get('damage_charge', 0)),
                                    notes="Rentable damaged"
                                ))
                    
                    room_ver_data = RoomVerificationData(
                        room_number=room.number,
                        consumables=[], # We can't pass ExtendedConsumableItem to Pydantic field validation effectively if strict
                        asset_damages=asset_damages
                    )
                    # Bypass pydantic validation for consumables list to hold our extended objects
                    room_ver_data.consumables = consumables 
                    
                    create_checkout_verification(db, new_checkout.id, room_ver_data, room.id, branch_id=branch_id)
            
            # 10. Process split payments
            if request.split_payments:
                process_split_payments(db, new_checkout.id, request.split_payments, branch_id=branch_id)
            elif request.payment_method:
                # Legacy single payment method
                payment_record = CheckoutPayment(
                    checkout_id=new_checkout.id,
                    payment_method=request.payment_method,
                    amount=grand_total,
                    branch_id=branch_id,
                    notes="Single payment method"
                )
                db.add(payment_record)
            
            # 11. Update billing status for food orders and services
            # Auto-complete pending orders/services when billing them
            db.query(FoodOrder).filter(
                FoodOrder.room_id == room.id, 
                FoodOrder.billing_status == "unbilled",
                FoodOrder.status != "cancelled"  # Don't complete cancelled orders
            ).update({"billing_status": "billed", "status": "completed"})
            
            db.query(AssignedService).filter(
                AssignedService.room_id == room.id, 
                AssignedService.billing_status == "unbilled",
                AssignedService.status != "cancelled" # Don't complete cancelled services
            ).update({
                "billing_status": "billed",
                "status": "completed",
                "last_used_at": datetime.utcnow()
            })
            
            # 12. Inventory Triggers
            # Check for CheckoutRequest first
            checkout_request = None
            if is_package:
                checkout_request = db.query(CheckoutRequestModel).filter(
                    CheckoutRequestModel.package_booking_id == booking.id,
                    CheckoutRequestModel.status == "completed"
                ).order_by(CheckoutRequestModel.id.desc()).first()
            else:
                checkout_request = db.query(CheckoutRequestModel).filter(
                    CheckoutRequestModel.booking_id == booking.id,
                    CheckoutRequestModel.status == "completed"
                ).order_by(CheckoutRequestModel.id.desc()).first()

            if checkout_request and checkout_request.inventory_data:
                # Convert inventory_data to list of objects with item_id and actual_consumed
                class SimpleConsumable:
                    def __init__(self, item_id, actual_consumed):
                        self.item_id = item_id
                        self.actual_consumed = actual_consumed
                
                consumables_list = []
                for item in checkout_request.inventory_data:
                    if float(item.get('used_qty', 0)) > 0:
                        consumables_list.append(SimpleConsumable(item.get('item_id'), float(item.get('used_qty', 0))))
                
                if consumables_list:
                    # Logic Removed: deduct_room_consumables is NOT needed here because 
                    # check_inventory_for_checkout already handled stock deduction and transaction creation.
                    # Calling it again causes double deduction (negative stock) and duplicate transactions.
                    pass
                    # deduct_room_consumables(
                    #    db, room.id, consumables_list, 
                    #    new_checkout.id, current_user.id if current_user else None
                    # )
            elif request.room_verifications:
                room_verification = next(
                    (rv for rv in request.room_verifications if rv.room_number == room.number),
                    None
                )
                if room_verification:
                    # Deduct consumables from inventory
                    deduct_room_consumables(
                        db, room.id, room_verification.consumables, 
                        new_checkout.id, created_by=current_user.id,
                        branch_id=branch_id
                    )

            # Clear remaining consumables from room inventory
            # Clear remaining consumables from room inventory - REMOVED
            # This logic was incorrectly setting GLOBAL stock to 0. Use proper transfer logic if needed.
            # room_items = ... (Removed)
            
            # Trigger linen cycle (move bed sheets/towels to laundry)
            trigger_linen_cycle(db, room.id, new_checkout.id, branch_id=branch_id)
            
            # 13. Update room status
            room.status = "Available"  # Room moves to "Dirty" status (ready for housekeeping)

            
            # 13.1. Return remaining consumables to warehouse - REMOVED PER USER REQUEST
            # Logic: We now rely on the 'return_items' service request created below.
            # Items stay in room inventory until staff completes the return service.
            # try:
            #     if room.inventory_location_id:
            #         from app.models.inventory import LocationStock, Location, InventoryTransaction, InventoryItem
            #         from sqlalchemy.orm import joinedload
            #         
            #         remaining = db.query(LocationStock).join(InventoryItem).filter(
            #             LocationStock.location_id == room.inventory_location_id,
            #             LocationStock.quantity > 0,
            #             InventoryItem.is_asset_fixed == False
            #         ).all()
            #         
            #         if remaining:
            #             warehouse = db.query(Location).filter(Location.location_type == "WAREHOUSE").first()
            #             if warehouse:
            #                 for item_stock in remaining:
            #                     qty = item_stock.quantity
            #                     item_name = item_stock.item.name if item_stock.item else f"Item #{item_stock.item_id}"
            #                     
            #                     wh_stock = db.query(LocationStock).filter(
            #                         LocationStock.location_id == warehouse.id,
            #                         LocationStock.item_id == item_stock.item_id
            #                     ).first()
            #                     
            #                     if wh_stock:
            #                         wh_stock.quantity += qty
            #                         wh_stock.last_updated = datetime.utcnow()
            #                     else:
            #                         db.add(LocationStock(
            #                             location_id=warehouse.id,
            #                             item_id=item_stock.item_id,
            #                             quantity=qty,
            #                             last_updated=datetime.utcnow()
            #                         ))
            #                     
            #                     item_stock.quantity = 0
            #                     item_stock.last_updated = datetime.utcnow()
            #                     print(f"[CLEANUP] Returned {qty} x {item_name} from Room {room.number}")
            # except Exception as e:
            #     print(f"[WARNING] Cleanup failed: {e}")
            
            # 13.5. Automatically create cleaning and refill service requests
            try:
                from app.curd import service_request as service_request_crud
                # Create cleaning service request
                service_request_crud.create_cleaning_service_request(
                    db, room.id, room.number, booking.guest_name, branch_id=branch_id
                )
                # Create refill service request with checkout_id to get consumables data
                service_request_crud.create_refill_service_request(
                    db, room.id, room.number, booking.guest_name, new_checkout.id, branch_id=branch_id
                )
                # Note: 'return_items' service request creation is REMOVED as it is now integrated into Checkout Verification
            except Exception as service_request_error:
                # Don't fail checkout if service request creation fails
                print(f"[WARNING] Failed to create service requests for room {room.number}: {service_request_error}")
            
            # 14. Check if all rooms in booking are checked out
            if is_package:
                remaining_rooms = [link.room for link in booking.rooms if link.room.status != "Available"]
            else:
                remaining_rooms = [link.room for link in booking.booking_rooms if link.room.status != "Available"]
            
            if not remaining_rooms:
                booking.status = "checked_out"
                booking.checked_out_at = datetime.utcnow()
            
            db.commit()
            db.refresh(new_checkout)
            
            # Generate PDF Bill and save it
            try:
                from app.utils.pdf_generator import generate_checkout_bill_pdf
                import os
                
                # Create bills directory if it doesn't exist
                bills_dir = os.path.join("uploads", "bills")
                os.makedirs(bills_dir, exist_ok=True)
                
                # Generate PDF filename
                pdf_filename = f"bill_{new_checkout.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                pdf_path = os.path.join(bills_dir, pdf_filename)
                
                # Generate the PDF
                generate_checkout_bill_pdf(new_checkout, bill_details_data, pdf_path)
                
                # Store the PDF path in the checkout record
                new_checkout.invoice_pdf_path = pdf_path
                db.commit()
                
                print(f"[CHECKOUT] PDF bill generated and saved: {pdf_path}")
            except Exception as pdf_error:
                # Don't fail checkout if PDF generation fails
                print(f"[WARNING] Failed to generate PDF bill for checkout {new_checkout.id}: {pdf_error}")
                import traceback
                traceback.print_exc()
            
            # 15. Automatically create journal entry for checkout (Scenario 2: Guest Checkout)
            # Debit: Bank Account / Cash | Credit: Room Revenue, Output CGST, Output SGST
            try:
                from app.utils.accounting_helpers import create_complete_checkout_journal_entry
                
                payment_method = request.payment_method or "cash"
                create_complete_checkout_journal_entry(
                    db=db,
                    checkout_id=new_checkout.id,
                    room_total=float(new_checkout.room_total or 0),
                    food_total=float(new_checkout.food_total or 0),
                    service_total=float(
                        (new_checkout.service_total or 0) + 
                        (new_checkout.consumables_charges or 0) + 
                        (new_checkout.inventory_charges or 0) + 
                        (new_checkout.asset_damage_charges or 0) + 
                        (new_checkout.key_card_fee or 0) + 
                        (new_checkout.late_checkout_fee or 0) +
                        (new_checkout.tips_gratuity or 0)
                    ),
                    package_total=float(new_checkout.package_total or 0),
                    tax_amount=float(new_checkout.tax_amount or 0),
                    discount_amount=float(new_checkout.discount_amount or 0),
                    grand_total=float(new_checkout.grand_total or 0),
                    guest_name=new_checkout.guest_name or "Guest",
                    room_number=new_checkout.room_number or room_number,
                    gst_rate=18.0,
                    payment_method=payment_method,
                    branch_id=branch_id,
                    created_by=current_user.id if current_user else None,
                    advance_amount=float(new_checkout.advance_deposit or 0)
                )

            except Exception as journal_error:
                # Log error but don't fail checkout
                import traceback
                error_msg = f"[WARNING] Failed to create journal entry for checkout {new_checkout.id}: {str(journal_error)}"
                print(error_msg)
                print(traceback.format_exc())
                # Store error in checkout notes for later reference
                if not new_checkout.notes:
                    new_checkout.notes = f"Journal entry creation failed: {str(journal_error)}"
                else:
                    new_checkout.notes += f"\nJournal entry creation failed: {str(journal_error)}"
            
        except Exception as e:
            db.rollback()
            error_detail = str(e)
            import traceback
            print(f"[ERROR] Checkout failed for room {room_number}, booking {booking.id}: {error_detail}")
            print(traceback.format_exc())
            
            # Check for unique constraint violation
            if "unique constraint" in error_detail.lower() or "duplicate key" in error_detail.lower() or "23505" in error_detail:
                # Try to find the existing checkout (check by booking_id first, then room_number)
                try:
                    existing_checkout = None
                    
                    # First check by booking_id (most reliable - unique constraint)
                    if not is_package:
                        existing_checkout = db.query(Checkout).filter(
                            Checkout.booking_id == booking.id
                        ).order_by(Checkout.created_at.desc()).first()
                    else:
                        existing_checkout = db.query(Checkout).filter(
                            Checkout.package_booking_id == booking.id
                        ).order_by(Checkout.created_at.desc()).first()
                    
                    # If not found by booking, check by room number and today
                    if not existing_checkout:
                        today = date.today()
                        existing_checkout = db.query(Checkout).filter(
                            Checkout.room_number == room_number,
                            func.date(Checkout.checkout_date) == today
                        ).order_by(Checkout.created_at.desc()).first()
                    
                    if existing_checkout:
                        # If room is still checked-in, this is an orphaned checkout - delete it
                        if room.status != "Available":
                            print(f"[CLEANUP] Found orphaned checkout {existing_checkout.id} for room {room_number} (room still checked-in). Deleting it.")
                            try:
                                # Unlink checkout requests first to avoid FK constraints
                                db.query(CheckoutRequestModel).filter(CheckoutRequestModel.checkout_id == existing_checkout.id).update({"checkout_id": None})
                                
                                db.delete(existing_checkout)
                                db.commit()
                                print(f"[CLEANUP] Successfully deleted orphaned checkout {existing_checkout.id}")
                                # After cleanup, we need to retry the checkout
                                # But we're in an exception handler, so we can't just continue
                                # Instead, raise a specific error that tells the user to retry
                                # The cleanup is done, so next attempt should work
                                raise HTTPException(
                                    status_code=409, 
                                    detail=f"Cleaned up an orphaned checkout record. Please click 'Complete Checkout' again - it should work now."
                                )
                            except HTTPException:
                                raise  # Re-raise HTTPException
                            except Exception as del_error:
                                print(f"[ERROR] Failed to delete orphaned checkout: {str(del_error)}")
                                db.rollback()
                                raise HTTPException(
                                    status_code=409, 
                                    detail=f"Found an orphaned checkout but couldn't delete it. Please contact support or try refreshing the page."
                                )
                        else:
                            # Room is available, checkout is valid - return it
                            print(f"[INFO] Found existing checkout {existing_checkout.id} for room {room_number}")
                            return CheckoutSuccess(
                                checkout_id=existing_checkout.id,
                                grand_total=existing_checkout.grand_total,
                                checkout_date=existing_checkout.checkout_date or existing_checkout.created_at
                            )
                except HTTPException:
                    raise  # Re-raise HTTPException from cleanup
                except Exception as lookup_error:
                    print(f"[WARNING] Error looking up existing checkout: {str(lookup_error)}")
                
                # If we get here and room is still checked-in, it means we couldn't find the orphaned checkout
                # But we got a unique constraint violation, so something is wrong
                # Try one more time to find and delete any checkout for this booking
                if room.status != "Available":
                    print(f"[ERROR] Unique constraint violation but couldn't find orphaned checkout. Room {room_number} is still checked-in.")
                    print(f"[CLEANUP] Attempting final cleanup for booking {booking.id}...")
                    try:
                        # Final attempt: delete ANY checkout for this booking, regardless of date
                        final_checkout = None
                        if not is_package:
                            final_checkout = db.query(Checkout).filter(Checkout.booking_id == booking.id).first()
                        else:
                            final_checkout = db.query(Checkout).filter(Checkout.package_booking_id == booking.id).first()
                        
                        if final_checkout:
                            # Delete related records
                            db.query(CheckoutVerification).filter(CheckoutVerification.checkout_id == final_checkout.id).delete()
                            db.query(CheckoutPayment).filter(CheckoutPayment.checkout_id == final_checkout.id).delete()
                            # Unlink checkout requests
                            db.query(CheckoutRequestModel).filter(CheckoutRequestModel.checkout_id == final_checkout.id).update({"checkout_id": None})
                            
                            db.delete(final_checkout)
                            db.commit()
                            print(f"[CLEANUP] Successfully deleted checkout {final_checkout.id} in final cleanup attempt")
                            raise HTTPException(
                                status_code=409,
                                detail=f"Found and cleaned up a conflicting checkout record. Please click 'Complete Checkout' again - it should work now."
                            )
                        else:
                            # No checkout found, but constraint violation occurred - might be invoice_number
                            raise HTTPException(
                                status_code=409, 
                                detail=f"Checkout failed due to a database constraint (possibly duplicate invoice number). Please try again - the system will generate a new invoice number."
                            )
                    except HTTPException:
                        raise
                    except Exception as final_error:
                        print(f"[ERROR] Final cleanup attempt failed: {str(final_error)}")
                        db.rollback()
                        raise HTTPException(
                            status_code=409, 
                            detail=f"Checkout failed due to a database constraint. Please refresh the page and try again, or contact support. Error: {str(final_error)}"
                        )
                else:
                    raise HTTPException(
                        status_code=409, 
                        detail=f"Checkout failed: A checkout record may already exist for this booking. Please refresh the page."
                    )
            raise HTTPException(status_code=500, detail=f"Checkout failed due to an internal error: {error_detail}")
        
        return CheckoutSuccess(
            checkout_id=new_checkout.id,
            grand_total=new_checkout.grand_total,
            checkout_date=new_checkout.checkout_date or new_checkout.created_at
        )
    
    else:
        # Multiple room checkout (entire booking)
        bill_data = _calculate_bill_for_entire_booking(db, room_number, branch_id=branch_id)

        booking = bill_data["booking"]
        all_rooms = bill_data["all_rooms"]
        charges = bill_data["charges"]
        is_package = bill_data["is_package"]
        room_ids = [room.id for room in all_rooms]

        # Check if booking is already checked out
        if booking.status in ["checked_out", "checked-out"]:
            raise HTTPException(status_code=409, detail=f"This booking has already been checked out.")
        
        # Validate booking is in a valid state for checkout
        if booking.status not in ['checked-in', 'checked_in', 'booked']:
            raise HTTPException(status_code=400, detail=f"Booking cannot be checked out. Current status: {booking.status}")
        
        # Check if a checkout record already exists for this booking TODAY (allow multiple checkouts on different dates)
        today = date.today()
        existing_checkout = None
        if not is_package:
            # First check for today's checkout
            existing_checkout = db.query(Checkout).filter(
                Checkout.booking_id == booking.id,
                func.date(Checkout.checkout_date) == today
            ).first()
            # If not found, check for any recent checkout (within last 7 days)
            if not existing_checkout:
                week_ago = date.today() - timedelta(days=7)
                existing_checkout = db.query(Checkout).filter(
                    Checkout.booking_id == booking.id,
                    func.date(Checkout.checkout_date) >= week_ago
                ).order_by(Checkout.created_at.desc()).first()
        else:
            existing_checkout = db.query(Checkout).filter(
                Checkout.package_booking_id == booking.id,
                func.date(Checkout.checkout_date) == today
            ).first()
            if not existing_checkout:
                week_ago = today - timedelta(days=7)
                existing_checkout = db.query(Checkout).filter(
                    Checkout.package_booking_id == booking.id,
                    func.date(Checkout.checkout_date) >= week_ago
                ).order_by(Checkout.created_at.desc()).first()
        
        if existing_checkout:
            # Return existing checkout instead of error
            print(f"[INFO] Found existing checkout {existing_checkout.id} for booking {booking.id}, returning it")
            return CheckoutSuccess(
                checkout_id=existing_checkout.id,
                grand_total=existing_checkout.grand_total,
                checkout_date=existing_checkout.checkout_date or existing_checkout.created_at
            )
        
        # Check if any rooms are already checked out
        already_checked_out_rooms = [room.number for room in all_rooms if room.status == "Available"]
        if already_checked_out_rooms:
            raise HTTPException(
                status_code=409, 
                detail=f"Some rooms in this booking are already checked out: {', '.join(already_checked_out_rooms)}. Please checkout remaining rooms individually or select rooms that are still checked in."
            )
        
        try:
            # ===== ENHANCED MULTIPLE ROOM CHECKOUT PROCESSING =====
            
            # 1. Process Pre-Checkout Verification for all rooms
            total_consumables_charges = 0.0
            total_asset_damage_charges = 0.0
            total_key_card_fee = 0.0
            
            # Charges from verify data if provided
            if request.room_verifications:
                # We will subtract DB computed values later and use fresh ones
                pass
            else:
                total_consumables_charges = charges.consumables_charges or 0.0
                total_asset_damage_charges = charges.asset_damage_charges or 0.0
            
            if request.room_verifications:
                for room_verification in request.room_verifications:
                    # Find the room
                    room_obj = next((r for r in all_rooms if r.number == room_verification.room_number), None)
                    if not room_obj:
                        continue
                    
                    # Process consumables audit
                    consumables_audit = process_consumables_audit(
                        db, room_obj.id, room_verification.consumables
                    )
                    total_consumables_charges += consumables_audit["total_charge"]
                    
                    # Process asset damages
                    asset_damage = process_asset_damage_check(room_verification.asset_damages)
                    total_asset_damage_charges += asset_damage["total_charge"]
                    
                    # Key card fee
                    if not room_verification.key_card_returned:
                        total_key_card_fee += 50.0
            
            # 2. Calculate Late Checkout Fee (based on average room rate)
            actual_checkout_time = request.actual_checkout_time or datetime.now()
            avg_room_rate = sum((r.price or 0.0) for r in all_rooms) / len(all_rooms) if all_rooms else 0.0
            late_checkout_fee = calculate_late_checkout_fee(
                booking.check_out,
                actual_checkout_time,
                avg_room_rate
            )
            
            # 3. Get Advance Deposit
            advance_deposit = getattr(booking, 'advance_deposit', 0.0) or 0.0
            
            # 4. Calculate final bill with all charges
            # Start with the DB-calculated total
            base_total = charges.total_due
            base_gst = charges.total_gst or 0
            
            # If we calculated fresh charges from verification data, subtract DB values to avoid double counting
            if request.room_verifications:
                base_total -= (charges.consumables_charges or 0)
                base_total -= (charges.asset_damage_charges or 0)
                
                base_gst -= (charges.consumables_gst or 0)
                base_gst -= (charges.asset_damage_gst or 0)
            else:
                # If no fresh verification, verify total_consumables_charges doesn't add to base_total again
                # Actually, in this case total_consumables_charges was set to charges.consumables_charges
                # So we MUST subtract them from base_total if we add them back in subtotal line
                base_total -= (charges.consumables_charges or 0)
                base_total -= (charges.asset_damage_charges or 0)
                base_gst -= (charges.consumables_gst or 0)
                base_gst -= (charges.asset_damage_gst or 0)
            
            subtotal = base_total + total_consumables_charges + total_asset_damage_charges + total_key_card_fee + late_checkout_fee
            
            # Recalculate GST
            consumables_gst = total_consumables_charges * 0.05
            asset_damage_gst = 0.0 # No GST on asset damages as per request
            
            tax_amount = base_gst + consumables_gst + asset_damage_gst
            
            discount_amount = max(0, request.discount_amount or 0)
            tips_gratuity = max(0, request.tips_gratuity or 0.0)
            
            grand_total_before_advance = max(0, subtotal + tax_amount - discount_amount + tips_gratuity)
            grand_total = max(0, grand_total_before_advance - advance_deposit)
            
            # 5. Get effective checkout date
            effective_checkout = bill_data.get("effective_checkout_date", booking.check_out)
            effective_checkout_datetime = datetime.combine(effective_checkout, datetime.min.time())
            
            # 6. Generate invoice number with retry logic
            invoice_number = None
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    invoice_number = generate_invoice_number(db)
                    existing_invoice = db.query(Checkout).filter(Checkout.invoice_number == invoice_number).first()
                    if not existing_invoice:
                        break
                    else:
                        print(f"[WARNING] Generated duplicate invoice number {invoice_number}, retrying...")
                        if attempt == max_retries - 1:
                            invoice_number = None
                except Exception as inv_error:
                    print(f"[WARNING] Error generating invoice number: {str(inv_error)}")
                    if attempt == max_retries - 1:
                        invoice_number = None
            
            # 6.5. Prepare bill breakdown snapshot
            from fastapi.encoders import jsonable_encoder
            charges_dict = jsonable_encoder(charges)
            bill_details_data = jsonable_encoder({
                "generated_at": datetime.now(),
                "charges_breakdown": charges_dict,
                "consumables_audit": {
                    "charges": total_consumables_charges,
                    "gst": consumables_gst,
                    "items": getattr(charges, "consumables_items", [])
                },
                "asset_damages": {
                    "charges": total_asset_damage_charges,
                    "gst": asset_damage_gst,
                    "items": getattr(charges, "asset_damages", [])
                },
                "inventory_usage": getattr(charges, "inventory_usage", []),
                "fixed_assets": getattr(charges, "fixed_assets", [])
            })
            
            # 7. Create enhanced checkout record
            new_checkout = Checkout(
                booking_id=booking.id if not is_package else None,
                package_booking_id=booking.id if is_package else None,
                room_total=charges.room_charges,
                food_total=charges.food_charges,
                service_total=charges.service_charges,
                package_total=charges.package_charges,
                tax_amount=tax_amount,
                discount_amount=discount_amount,
                grand_total=grand_total,
                payment_method=request.payment_method or "cash",
                payment_status="Paid",
                guest_name=booking.guest_name,
                room_number=", ".join(sorted([room.number for room in all_rooms])),
                checkout_date=effective_checkout_datetime,
                # Enhanced fields
                late_checkout_fee=late_checkout_fee,
                consumables_charges=total_consumables_charges,
                inventory_charges=getattr(charges, "inventory_charges", 0.0) or 0.0,
                asset_damage_charges=total_asset_damage_charges,
                key_card_fee=total_key_card_fee,
                advance_deposit=advance_deposit,
                tips_gratuity=tips_gratuity,
                guest_gstin=request.guest_gstin,
                is_b2b=request.is_b2b or False,
                invoice_number=invoice_number,
                bill_details=bill_details_data,
                branch_id=branch_id
            )
            # If invoice_number wasn't generated, create one based on checkout ID after flush
            if not invoice_number:
                db.add(new_checkout)
                db.flush()  # Flush to get checkout ID
                invoice_number = f"INV-{new_checkout.id:06d}"
                new_checkout.invoice_number = invoice_number
            else:
                db.add(new_checkout)
                db.flush()  # Flush to get checkout ID
            
            # 8. Create checkout verification records for all rooms
            if request.room_verifications:
                for room_verification in request.room_verifications:
                    room_obj = next((r for r in all_rooms if r.number == room_verification.room_number), None)
                    if room_obj:
                        create_checkout_verification(db, new_checkout.id, room_verification, room_obj.id)
                        # Deduct consumables (Moved from step 11 to avoid double trigger)
                        deduct_room_consumables(
                            db, room_obj.id, room_verification.consumables, 
                            new_checkout.id, created_by=current_user.id,
                            branch_id=branch_id
                        )
            
            # Deduct from CheckoutRequest if available
            if is_package:
                checkout_requests = db.query(CheckoutRequestModel).filter(
                    CheckoutRequestModel.package_booking_id == booking.id
                ).all()
            else:
                checkout_requests = db.query(CheckoutRequestModel).filter(
                    CheckoutRequestModel.booking_id == booking.id
                ).all()
                
            for checkout_request in checkout_requests:
                if checkout_request.inventory_data:
                    # Find the room for this request
                    room_obj = next((r for r in all_rooms if r.number == checkout_request.room_number), None)
                    if room_obj:
                         # Convert inventory_data to list of objects with item_id and actual_consumed
                        class SimpleConsumable:
                            def __init__(self, item_id, actual_consumed):
                                self.item_id = item_id
                                self.actual_consumed = actual_consumed
                        
                        consumables_list = []
                        for item in checkout_request.inventory_data:
                            if float(item.get('used_qty', 0)) > 0:
                                consumables_list.append(SimpleConsumable(item.get('item_id'), float(item.get('used_qty', 0))))
                        
                        if consumables_list:
                            # Logic Removed: deduct_room_consumables is NOT needed here because 
                            # check_inventory_for_checkout already handled stock deduction and transaction creation.
                            # Calling it again causes double deduction (negative stock) and duplicate transactions.
                            pass
                            # deduct_room_consumables(
                            #    db, room_obj.id, consumables_list, 
                            #    new_checkout.id, current_user.id if current_user else None
                            # )
            
            # Link checkout requests to this checkout
            for checkout_request in checkout_requests:
                checkout_request.checkout_id = new_checkout.id
            
            # Clear remaining consumables from room inventory - REMOVED
            # This logic was incorrectly setting GLOBAL stock to 0. Use proper transfer logic if needed.
            
            # 9. Process split payments
            if request.split_payments:
                process_split_payments(db, new_checkout.id, request.split_payments, branch_id=branch_id)
            elif request.payment_method:
                payment_record = CheckoutPayment(
                    checkout_id=new_checkout.id,
                    payment_method=request.payment_method,
                    amount=grand_total,
                    notes="Single payment method",
                    branch_id=branch_id
                )
                db.add(payment_record)
            
            # 10. Update billing status
            # Auto-complete pending orders/services when billing them
            db.query(FoodOrder).filter(
                FoodOrder.room_id.in_(room_ids), 
                FoodOrder.billing_status == "unbilled",
                FoodOrder.status != "cancelled"  # Don't complete cancelled orders
            ).update({"billing_status": "billed", "status": "completed"})
            
            db.query(AssignedService).filter(
                AssignedService.room_id.in_(room_ids), 
                AssignedService.billing_status == "unbilled",
                AssignedService.status != "cancelled" # Don't complete cancelled services
            ).update({
                "billing_status": "billed",
                "status": "completed",
                "last_used_at": datetime.utcnow()
            })
            
            # 11. Inventory Triggers for all rooms (Linen only, consumables handled in Step 8)
            if request.room_verifications:
                for room_verification in request.room_verifications:
                    room_obj = next((r for r in all_rooms if r.number == room_verification.room_number), None)
                    if room_obj:
                        trigger_linen_cycle(db, room_obj.id, new_checkout.id, branch_id=branch_id)
            
            # 12. Update booking and room statuses
            booking.status = "checked_out"
            booking.checked_out_at = datetime.utcnow()
            booking.total_amount = grand_total
            db.query(Room).filter(Room.id.in_(room_ids)).update({"status": "Available"})
            
            # 12.5. Automatically create cleaning and refill service requests for all rooms
            try:
                from app.curd import service_request as service_request_crud
                for room in all_rooms:
                    try:
                        # Create cleaning service request
                        service_request_crud.create_cleaning_service_request(
                            db, room.id, room.number, booking.guest_name, branch_id=branch_id
                        )
                        # Create refill service request with checkout_id to get consumables data
                        service_request_crud.create_refill_service_request(
                            db, room.id, room.number, booking.guest_name, new_checkout.id, branch_id=branch_id
                        )
                    except Exception as room_service_error:
                        # Don't fail checkout if service request creation fails for one room
                        print(f"[WARNING] Failed to create service requests for room {room.number}: {room_service_error}")

            except Exception as service_error:
                # Don't fail checkout if service request creation fails
                print(f"[WARNING] Failed to create service requests: {service_error}")

            db.commit()
            db.refresh(new_checkout)
            
            # Generate PDF Bill and save it
            try:
                from app.utils.pdf_generator import generate_checkout_bill_pdf
                import os
                
                # Create bills directory if it doesn't exist
                bills_dir = os.path.join("uploads", "bills")
                os.makedirs(bills_dir, exist_ok=True)
                
                # Generate PDF filename
                pdf_filename = f"bill_{new_checkout.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                pdf_path = os.path.join(bills_dir, pdf_filename)
                
                # Generate the PDF
                generate_checkout_bill_pdf(new_checkout, bill_details_data, pdf_path)
                
                # Store the PDF path in the checkout record
                new_checkout.invoice_pdf_path = pdf_path
                db.commit()
                
                print(f"[CHECKOUT] PDF bill generated and saved: {pdf_path}")
            except Exception as pdf_error:
                # Don't fail checkout if PDF generation fails
                print(f"[WARNING] Failed to generate PDF bill for checkout {new_checkout.id}: {pdf_error}")
                import traceback
                traceback.print_exc()
            
            # 12. Automatically create journal entry for checkout (Scenario 2: Guest Checkout)
            # Debit: Bank Account / Cash | Credit: Room Revenue, Output CGST, Output SGST
            # Only create if grand_total > 0 and we have valid data
            if new_checkout.grand_total and new_checkout.grand_total > 0:
                try:
                    from app.utils.accounting_helpers import create_complete_checkout_journal_entry
                    
                    payment_method = request.payment_method or "cash"
                    result = create_complete_checkout_journal_entry(
                        db=db,
                        checkout_id=new_checkout.id,
                        room_total=float(new_checkout.room_total or 0),
                        food_total=float(new_checkout.food_total or 0),
                        service_total=float(
                            (new_checkout.service_total or 0) + 
                            (new_checkout.consumables_charges or 0) + 
                            (new_checkout.inventory_charges or 0) + 
                            (new_checkout.asset_damage_charges or 0) + 
                            (new_checkout.key_card_fee or 0) + 
                            (new_checkout.late_checkout_fee or 0) +
                            (new_checkout.tips_gratuity or 0)
                        ),
                        package_total=float(new_checkout.package_total or 0),
                        tax_amount=float(new_checkout.tax_amount or 0),
                        discount_amount=float(new_checkout.discount_amount or 0),
                        grand_total=float(new_checkout.grand_total or 0),
                        guest_name=new_checkout.guest_name or "Guest",
                        room_number=room_number,  # Primary room number
                        gst_rate=18.0,
                        payment_method=payment_method,
                        created_by=current_user.id if current_user else None,
                        advance_amount=float(new_checkout.advance_deposit or 0),
                        branch_id=branch_id
                    )
                    if result is None:
                        print(f"[INFO] Journal entry not created for checkout {new_checkout.id} (ledgers may not be set up yet)")
                except Exception as journal_error:
                    import traceback
                    print(f"[WARNING] Failed to create journal entry for checkout {new_checkout.id}: {str(journal_error)}\n{traceback.format_exc()}")

        except Exception as e:
            db.rollback()
            error_detail = str(e)
            # Check for unique constraint violation (postgres error code 23505)
            if "unique constraint" in error_detail.lower() or "duplicate key" in error_detail.lower() or "23505" in error_detail:
                raise HTTPException(
                    status_code=409, 
                    detail="This booking has already been checked out. A checkout record already exists for this booking."
                )
            raise HTTPException(status_code=500, detail=f"Checkout failed due to an internal error: {error_detail}")

        # Return the data from the newly created checkout record
        return CheckoutSuccess(
            checkout_id=new_checkout.id,
            grand_total=new_checkout.grand_total,
            checkout_date=new_checkout.checkout_date or new_checkout.created_at
        )
