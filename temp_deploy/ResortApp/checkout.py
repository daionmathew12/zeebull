from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from typing import List, Optional
from datetime import date, datetime, timedelta

# Assume your utility and model imports are set up correctly
from app.utils.auth import get_db, get_current_user
from app.models.room import Room
from app.models.booking import Booking, BookingRoom
from app.models.Package import Package, PackageBooking, PackageBookingRoom
from app.models.user import User
from app.models.foodorder import FoodOrder, FoodOrderItem
from app.models.service import AssignedService, Service
from app.models.checkout import Checkout, CheckoutVerification, CheckoutPayment, CheckoutRequest as CheckoutRequestModel
from app.models.inventory import InventoryItem, StockIssue, StockIssueDetail, AssetMapping
from app.schemas.checkout import BillSummary, BillBreakdown, CheckoutFull, CheckoutSuccess, CheckoutRequest, InventoryCheckRequest
from app.utils.checkout_helpers import (
    calculate_late_checkout_fee, process_consumables_audit, process_asset_damage_check,
    deduct_room_consumables, trigger_linen_cycle, create_checkout_verification,
    process_split_payments, generate_invoice_number, calculate_gst_breakdown,
    calculate_consumable_charge
)

router = APIRouter(prefix="/bill", tags=["checkout"])

# IMPORTANT: To support this new logic, you must update your BillSummary schema.
# In `app/schemas/checkout.py`, please change the `room_number: str` field to:
# room_numbers: List[str]


@router.post("/checkout-request")
def create_checkout_request(
    room_number: str = Query(..., description="Room number to create checkout request for"),
    checkout_mode: str = Query("multiple", description="Checkout mode: 'single' or 'multiple'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a checkout request for inventory verification before checkout.
    """
    # Find the booking for this room
    room = db.query(Room).filter(Room.number == room_number).first()
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
    
    # Check if there's already a pending checkout request
    existing_request = None
    if is_package:
        existing_request = db.query(CheckoutRequestModel).filter(
            CheckoutRequestModel.package_booking_id == booking.id,
            CheckoutRequestModel.status.in_(["pending", "inventory_checked"])
        ).first()
    else:
        existing_request = db.query(CheckoutRequestModel).filter(
            CheckoutRequestModel.booking_id == booking.id,
            CheckoutRequestModel.status.in_(["pending", "inventory_checked"])
        ).first()
    
    if existing_request:
        return {
            "message": "Checkout request already exists",
            "request_id": existing_request.id,
            "status": existing_request.status,
            "inventory_checked": existing_request.inventory_checked
        }
    
    # Create new checkout request
    try:
        requested_by_name = getattr(current_user, 'name', None) or getattr(current_user, 'email', None) or "system"
        
        new_request = CheckoutRequestModel(
            booking_id=booking.id if not is_package else None,
            package_booking_id=booking.id if is_package else None,
            room_number=room_number,
            guest_name=booking.guest_name,
            status="pending",
            requested_by=requested_by_name,
            inventory_checked=False
        )
        
        db.add(new_request)
        db.commit()
        db.refresh(new_request)
        
        return {
            "message": "Checkout request created successfully",
            "request_id": new_request.id,
            "status": new_request.status,
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
    current_user: User = Depends(get_current_user)
):
    """
    Get checkout request status for a room.
    """
    room = db.query(Room).filter(Room.number == room_number).first()
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
        return {"exists": False, "status": None}
    
    # Find checkout request
    checkout_request = None
    if is_package:
        checkout_request = db.query(CheckoutRequestModel).filter(
            CheckoutRequestModel.package_booking_id == booking.id
        ).order_by(CheckoutRequestModel.id.desc()).first()
    else:
        checkout_request = db.query(CheckoutRequestModel).filter(
            CheckoutRequestModel.booking_id == booking.id
        ).order_by(CheckoutRequestModel.id.desc()).first()
    
    if not checkout_request:
        return {"exists": False, "status": None}
    
    return {
        "exists": True,
        "request_id": checkout_request.id,
        "status": checkout_request.status,
        "inventory_checked": checkout_request.inventory_checked,
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
    current_user: User = Depends(get_current_user)
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
    current_user: User = Depends(get_current_user)
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
    current_user: User = Depends(get_current_user)
):
    """
    Get current inventory details for a checkout request room.
    """
    def debug_log(msg):
        try:
            with open("checkout_debug.log", "a") as f:
                f.write(f"[{datetime.utcnow()}] {msg}\n")
        except: pass

    debug_log(f"START Processing Req {request_id}")

    checkout_request = db.query(CheckoutRequestModel).filter(CheckoutRequestModel.id == request_id).first()
    if not checkout_request:
        debug_log(f"Req {request_id} not found")
        raise HTTPException(status_code=404, detail="Checkout request not found")
    
    room = db.query(Room).filter(Room.number == checkout_request.room_number).first()
    if not room:
        debug_log(f"Room {checkout_request.room_number} not found")
        raise HTTPException(status_code=404, detail=f"Room {checkout_request.room_number} not found")
    
    # Get inventory items for the room location
    from app.models.inventory import Location
    
    if not room.inventory_location_id:
        debug_log(f"Room {room.number} has NO Inventory Location ID")
        return {
            "room_number": checkout_request.room_number,
            "items": [],
            "message": "No inventory location assigned to this room"
        }
    
    # Get location items using the inventory API endpoint logic
    location = db.query(Location).filter(Location.id == room.inventory_location_id).first()
    if not location:
        debug_log(f"Location obj not found for ID {room.inventory_location_id}")
        return {
            "room_number": checkout_request.room_number,
            "items": [],
            "message": "Inventory location not found"
        }
    
    try:
        from app.models.inventory import InventoryItem, LocationStock, StockIssue, StockIssueDetail, AssetMapping, AssetRegistry
        from app.curd import inventory as inventory_crud
        
        location_id = location.id
        debug_log(f"Room {room.number} using Location {location.name} (ID: {location_id})")
        
        # 1. Get items from LocationStock (Primary Source)
        try:
            q = db.query(LocationStock).filter(
                LocationStock.location_id == location_id,
                LocationStock.quantity > 0
            )
            debug_log(f"ORM QUERY: {str(q)}")
            debug_log(f"ORM Filters: Loc={location_id} (Type: {type(location_id)}), Qty>0")
            location_stocks = q.all()
            debug_log(f"Found {len(location_stocks)} LocationStock items")

            if len(location_stocks) == 0:
                # Probe: Is the table empty for ORM?
                probe_count = db.query(LocationStock).count()
                debug_log(f"ORM Table Count: {probe_count}")
                
        except Exception as e:
            debug_log(f"ORM QUERY ERROR: {e}")
            location_stocks = []

        # 2. Get items assigned to this location via asset mappings
        asset_mappings = db.query(AssetMapping).filter(
            AssetMapping.location_id == location_id,
            AssetMapping.is_active == True
        ).all()
        debug_log(f"Found {len(asset_mappings)} AssetMapping items")
        
        # 3. Get items from asset registry
        asset_registry = db.query(AssetRegistry).filter(
            AssetRegistry.current_location_id == location_id
        ).all()
        debug_log(f"Found {len(asset_registry)} AssetRegistry items")
        
        # DEBUG: Direct RAW SQL Check to bypass ORM
        try:
            from sqlalchemy import text
            from app.database import SQLALCHEMY_DATABASE_URL
            debug_log(f"DB URL: {SQLALCHEMY_DATABASE_URL}")
            
            # Check total rows in location_stocks for this location
            raw_count = db.execute(text(f"SELECT count(*) FROM location_stocks WHERE location_id = {location_id}")).scalar()
            debug_log(f"RAW CNT All stocks for Loc {location_id}: {raw_count}")
            
            # Check > 0 rows
            raw_pos_count = db.execute(text(f"SELECT count(*) FROM location_stocks WHERE location_id = {location_id} AND quantity > 0")).scalar()
            debug_log(f"RAW CNT >0 stocks for Loc {location_id}: {raw_pos_count}")
            
            if raw_pos_count > 0:
                rows = db.execute(text(f"SELECT id, location_id, item_id, quantity FROM location_stocks WHERE location_id = {location_id} AND quantity > 0")).fetchall()
                debug_log(f"RAW ROWS: {rows}")
                
        except Exception as e:
            debug_log(f"RAW CHECK FAILED: {str(e)}")

        # Combine all items
        items_dict = {}
        
        # Process LocationStock
        debug_log(f"Starting Loop over {len(location_stocks)} stocks")
        for stock in location_stocks:
            item = stock.item
            # debug_log(f"Processing Stock ID {stock.id}, Item ID {stock.item_id}, Qty {stock.quantity}, ItemObj: {item}")
            if not item:
                 debug_log(f"WARNING: Stock {stock.id} has NO ITEM relation (item_id {stock.item_id})")
            
            if item:
                debug_log(f"Stock {stock.id}: Item {item.name}, Qty {stock.quantity}")
                category = inventory_crud.get_category_by_id(db, item.category_id)
                
                # CRITICAL FIX: Check if this item is permanently mapped to this room
                # We need to track the mapped quantity separately
                permanently_mapped_qty = 0.0
                try:
                    from app.models.inventory import AssetMapping
                    permanent_mapping = db.query(AssetMapping).filter(
                        AssetMapping.location_id == location_id,
                        AssetMapping.item_id == item.id,
                        AssetMapping.is_active == True
                    ).first()
                    if permanent_mapping:
                        permanently_mapped_qty = float(permanent_mapping.quantity or 1)
                        debug_log(f"Item {item.name} has {permanently_mapped_qty} units PERMANENTLY MAPPED")
                except Exception as e:
                    debug_log(f"Error checking permanent mapping: {e}")
                
                # Fetch all issue details ordered by date DESC for this item/location
                issue_details = db.query(StockIssueDetail).join(StockIssue).filter(
                    StockIssue.destination_location_id == location_id,
                    StockIssueDetail.item_id == item.id
                ).order_by(StockIssue.issue_date.desc()).all()
                
                # Calculate total stock from LocationStock
                current_stock_qty = float(stock.quantity)
                
                # Separate the stock into:
                # 1. Permanently mapped quantity (from Asset Allocation) - always fixed
                # 2. Issued quantity (from Stock Issues) - can be rental or standard
                
                # The permanently mapped quantity should be excluded from rental logic
                issued_stock_qty = max(0, current_stock_qty - permanently_mapped_qty)
                
                debug_log(f"Item {item.name}: Total={current_stock_qty}, Mapped={permanently_mapped_qty}, Issued={issued_stock_qty}")
                
                # Split ONLY the issued stock into Rented vs Standard
                rented_issues = [d for d in issue_details if (d.rental_price and d.rental_price > 0) or d.is_payable]
                standard_issues = [d for d in issue_details if not ((d.rental_price and d.rental_price > 0) or d.is_payable)]
                
                # Determine split quantities based on ISSUED stock (not total)
                total_rented_issue_qty = sum(float(d.issued_quantity) for d in rented_issues)
                
                rented_stock_qty = min(issued_stock_qty, total_rented_issue_qty)
                standard_stock_qty = max(0, issued_stock_qty - rented_stock_qty)
                
                # Helper to process a batch
                def process_batch(qty, issues, key_suffix, is_rent_split):
                    remaining = float(qty)
                    payable_qty = 0.0
                    complimentary_qty = 0.0
                    
                    issue_idx = 0
                    while remaining > 0:
                        take = 0
                        if issue_idx < len(issues):
                            issue = issues[issue_idx]
                            needed = float(issue.issued_quantity)
                            take = min(remaining, needed)
                            # Check if payable
                            is_pay = False
                            if (getattr(issue, "rental_price", 0) or 0) > 0: is_pay = True
                            if getattr(issue, "is_payable", False): is_pay = True
                            
                            if is_pay:
                                payable_qty += take
                            else:
                                complimentary_qty += take
                            issue_idx += 1
                        else:
                            # Surplus stock is usually complimentary (or just unconsumed stock)
                            complimentary_qty += remaining
                            take = remaining
                        remaining -= take
                    
                    key = f"{item.id}{key_suffix}"
                    display_name = item.name
                    # Name Decoration
                    if is_asset_type:
                        if is_rent_split: display_name += " (Rented)"
                    else:
                        if payable_qty > 0 and complimentary_qty > 0: display_name += " (Comp/Payable)"
                        elif payable_qty > 0: display_name += " (Payable)"
                    
                    if key not in items_dict:
                        is_fixed = getattr(item, "is_asset_fixed", False)
                        # Determine is_rentable flag for UI logic
                        is_rentable = is_rent_split or getattr(item, "is_rentable", False)
                        
                        # CRITICAL FIX: If identified as Asset type and NOT fixed, force rentable
                        # This ensures it goes to "Rentable/Returnable" section instead of Consumables
                        if is_asset_type and not is_fixed:
                            is_rentable = True
                        
                        items_dict[key] = {
                            "id": item.id,
                            "item_code": item.item_code,
                            "item_name": display_name,
                            "current_stock": 0.0,
                            "complimentary_qty": 0.0,
                            "payable_qty": 0.0,
                            "category_id": item.category_id,
                            "is_payable": is_rent_split or (payable_qty > 0),
                            "item_type": item_type_str,
                            "check_stock_compatibility": getattr(item, "check_stock_compatibility", False),
                            "item_id": item.id,
                            "unit": item.unit,
                            "unit_price": item.unit_price or 0,
                            "charge_per_unit": item.selling_price or item.unit_price or 0,
                            "complimentary_limit": item.complimentary_limit or 0,
                            "is_rentable": is_rentable,
                            "is_fixed_asset": is_fixed
                        }
                    
                    items_dict[key]["current_stock"] += qty
                    items_dict[key]["complimentary_qty"] += complimentary_qty
                    items_dict[key]["payable_qty"] += payable_qty
                if permanently_mapped_qty > 0:
                    key = f"asset_mapped_{item.id}"
                    is_fixed = item.is_asset_fixed or (category and getattr(category, 'is_asset_fixed', False))
                    
                    items_dict[key] = {
                        "id": item.id,
                        "item_id": item.id,
                        "item_name": item.name,
                        "name": item.name,
                        "item_code": item.item_code,
                        "current_stock": permanently_mapped_qty,
                        "complimentary_qty": permanently_mapped_qty,
                        "payable_qty": 0,
                        "stock_value": permanently_mapped_qty * (item.unit_price or 0),
                        "unit": item.unit,
                        "unit_price": item.unit_price or 0,
                        "charge_per_unit": item.selling_price or item.unit_price or 0,
                        "cost_per_unit": item.selling_price or item.unit_price or 0,
                        "replacement_cost": item.selling_price or item.unit_price or 0,
                        "is_fixed_asset": True,  # ALWAYS fixed
                        "track_laundry_cycle": item.track_laundry_cycle,
                        "is_rentable": False,  # NEVER rentable
                        "is_payable": False,
                        "complimentary_limit": item.complimentary_limit or 0
                    }
                    debug_log(f"Added MAPPED entry: {key} with qty {permanently_mapped_qty}")
                
                # 2. Process Rented and Standard Good batches
                # Define issues lists
                good_rented_issues = [d for d in issue_details if (getattr(d, "rental_price", 0) or 0) > 0]
                good_issues = [d for d in issue_details if d not in good_rented_issues]
                
                is_asset_type = False
                # Improved Asset Detection
                # 1. Check if rentable (Rentals are assets)
                if getattr(item, "is_rentable", False):
                    is_asset_type = True
                # 2. Check if Fixed Asset
                elif getattr(item, "is_asset_fixed", False):
                    is_asset_type = True
                # 3. Check Category attributes (handle missing "type" attr safely)
                elif item.category:
                    cat_type = getattr(item.category, "type", "") or ""
                    if cat_type == "asset":
                         is_asset_type = True
                    elif getattr(item.category, "is_asset_fixed", False):
                         is_asset_type = True
                    # Hack: Check known asset categories by name if type is missing
                    elif "appliance" in getattr(item.category, "name", "").lower():
                         is_asset_type = True
                
                item_type_str = "Asset" if is_asset_type else "Consumable"
                
                if is_asset_type:
                    if rented_stock_qty > 0:
                        process_batch(rented_stock_qty, good_rented_issues, "_rented", True)
                    if standard_stock_qty > 0:
                        process_batch(standard_stock_qty, good_issues, "", False)
                else:
                    # Consumables: Process ALL issues (issue_details) in one batch
                    process_batch(issued_stock_qty, issue_details, "", False)
        for mapping in asset_mappings:
            item = inventory_crud.get_item_by_id(db, mapping.item_id)
            if item:
                stock_key = f"item_{item.id}"
                
                # Check if this item was already added via LocationStock
                if stock_key in items_dict:
                    # MERGE: Update the existing entry to ensure it's treated as a Fixed Asset
                    items_dict[stock_key].update({
                        "type": "asset",           # Force type to asset
                        "is_fixed_asset": True,    # Force fixed asset flag
                        "is_rentable": False,      # Force not rentable
                        "source": items_dict[stock_key].get("source", "") + ", Asset Mapping"
                    })
                    # We do NOT add a new asset_mapped_ entry to avoid duplicates
                else:
                    # Add as new entry if not in LocationStock
                    # Use standard key format to ensure consistency
                    key = f"asset_mapped_{item.id}"
                    
                    category = inventory_crud.get_category_by_id(db, item.category_id)
                    items_dict[key] = {
                        "id": item.id,
                        "item_name": item.name,
                        "name": item.name,
                        "item_id": item.id, # frontend compatibility
                        "item_code": item.item_code,
                        "current_stock": mapping.quantity or 1,
                        "complimentary_qty": mapping.quantity or 1, # Mapped assets usually complimentary/standard
                        "payable_qty": 0,
                        "stock_value": (item.unit_price or 0) * (mapping.quantity or 1),
                        "unit": item.unit,
                        "unit_price": item.unit_price or 0,
                        "charge_per_unit": item.selling_price or item.unit_price or 0,
                        "replacement_cost": item.selling_price or item.unit_price or 0, # frontend compatibility
                        "is_fixed_asset": True,  # Mapped assets are always fixed
                        "track_laundry_cycle": item.track_laundry_cycle,
                        "is_rentable": False,  # Mapped assets are never rentable
                        "is_payable": False,
                        "complimentary_limit": item.complimentary_limit or 0
                    }
                    debug_log(f"Added AssetMapping entry: {key} for {item.name}")
        
        # Process Asset Registry
        for asset in asset_registry:
            item = asset.item
            if item:
                key = f"registry_{asset.id}"
                category = inventory_crud.get_category_by_id(db, item.category_id)
                is_fixed = item.is_asset_fixed or (category and getattr(category, 'is_asset_fixed', False))
                
                items_dict[key] = {
                    "id": item.id,
                    "item_id": item.id, # frontend compatibility
                    "item_name": item.name,
                    "name": item.name,
                    "item_code": item.item_code,
                    "current_stock": 1,
                    "complimentary_qty": 1,
                    "payable_qty": 0,
                    "stock_value": item.unit_price or 0,
                    "unit": item.unit,
                    "unit_price": item.unit_price or 0,
                    "charge_per_unit": item.selling_price or item.unit_price or 0,
                    "replacement_cost": item.selling_price or item.unit_price or 0, # frontend compatibility
                    "is_fixed_asset": is_fixed,
                    "track_laundry_cycle": item.track_laundry_cycle,
                    "is_rentable": False,
                    "is_payable": False,
                    "complimentary_limit": item.complimentary_limit or 0
                }

        # Separate items into fixed assets and others for frontend clarity if needed
        items_list = list(items_dict.values())

        # But crucially, we must ensure 'fixed_assets' key exists if frontend expects it
        fixed_assets = [item for item in items_list if item.get('is_fixed_asset')]
        
        return {
            "room_number": checkout_request.room_number,
            "guest_name": checkout_request.guest_name,
            "items": items_list,
            "fixed_assets": fixed_assets, # Added back for frontend compatibility
            "location_name": location.name
        }
    except Exception as e:
        import traceback
        print(f"Error getting inventory details: {traceback.format_exc()}")
        return {
            "room_number": checkout_request.room_number,
            "items": [],
            "error": str(e)
        }


@router.post("/checkout-request/{request_id}/check-inventory")
async def handleCompleteCheckoutRequest(
    request_id: int,
    payload: InventoryCheckRequest, # Assuming InventoryCheckRequest is the correct payload type based on original code
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark inventory as checked and complete the checkout request.
    Stores used/missing items in inventory_data.
    Calculates charges for missing items.
    """

    from app.models.inventory import InventoryItem
    
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
    missing_items_details = []
    
    inventory_data_with_charges = []
    
    # Safety check: ensure we have items to process
    return_issues_map = {} # Map destination_loc_id -> StockIssue object
    import traceback
    try:
        # Fetch Room Object once (used for validation and stock issue lookup)
        room_room = db.query(Room).filter(Room.number == checkout_request.room_number).first()

        if payload.items:
            for item in payload.items:
                item_dict = item.dict()
                
                # Populate item details even if missing_qty is 0
                inv_item = db.query(InventoryItem).options(joinedload(InventoryItem.category)).filter(InventoryItem.id == item.item_id).first()
                
                if not inv_item:
                    print(f"[CHECKOUT ERROR] Item ID {item.item_id} not found in database. Skipping.")
                    continue

                if inv_item:
                     item_dict['item_name'] = inv_item.name
                     item_dict['item_code'] = inv_item.item_code
                
                
                # --- STOCK RETURN LOGIC & USAGE CALCULATION ---
                
                # Helper flags
                is_fixed_asset = getattr(inv_item, 'is_asset_fixed', False)
                # Fallback: Check if category is marked as fixed asset
                if not is_fixed_asset and inv_item.category and getattr(inv_item.category, 'is_asset_fixed', False):
                    is_fixed_asset = True
                    
                is_rental = False
                # Safe access to category name
                if inv_item and inv_item.category and getattr(inv_item.category, 'name', None) and "rental" in inv_item.category.name.lower():
                    is_rental = True
                    
                # Check if this item is explicitly mapped as an asset to this room (Asset Allocation)
                # Use the flags passed from the frontend (payload) as primary source of truth
                is_mapped_asset = item.is_fixed_asset and not item.is_rentable
                is_rental = item.is_rentable
                
                # Fallback/Validation if not explicitly marked (Old frontend or missing metadata)
                if not is_rental and not is_mapped_asset:
                    # room_room already fetched above
                    if room_room and room_room.inventory_location_id:
                        from app.models.inventory import AssetMapping, StockIssue, StockIssueDetail
                        from sqlalchemy import or_
                        
                        # Check 1: Is it a Mapped Asset (Permanent)?
                        existing_mapping = db.query(AssetMapping).filter(
                            AssetMapping.location_id == room_room.inventory_location_id,
                            AssetMapping.item_id == item.item_id,
                            AssetMapping.is_active == True
                        ).first()
                        if existing_mapping:
                            is_mapped_asset = True
                        
                        # Check 2: Is it a Rental (Issued with Price)?
                        rental_issue = db.query(StockIssueDetail).join(StockIssue).filter(
                            StockIssue.destination_location_id == room_room.inventory_location_id,
                            StockIssueDetail.item_id == item.item_id,
                            or_(StockIssueDetail.rental_price > 0, StockIssueDetail.is_payable == True)
                        ).first()
                        if rental_issue:
                            is_rental = True
                
                print(f"[CHECKOUT] Item {inv_item.name}: is_rental={is_rental}, is_mapped_asset={is_mapped_asset}")


                
                # Logic: We process return/deduction for:
                # 1. Consumables (always returned/cleared)
                # 2. Rentals (ALWAYS returned to source, even if they're fixed assets)
                # 3. Temporary fixed assets (issued but not permanently mapped)
                # 
                # Items that STAY in room:
                # - Permanently mapped assets (TVs, ACs, etc. in Asset Allocation)
                # - Fixed assets that are NOT rentals AND NOT temporarily issued
                
                should_process_return = True
                
                # CRITICAL FIX: Rentals MUST be returned regardless of asset type
                if is_rental:
                    should_process_return = True
                    print(f"[CHECKOUT] Item {inv_item.name} is a RENTAL - will be RETURNED to source")
                elif is_mapped_asset:
                    # Permanently mapped assets stay in room (unless they're rentals, handled above)
                    should_process_return = False
                    print(f"[CHECKOUT] Item {inv_item.name} is a MAPPED PERMANENT ASSET - will NOT be cleared from room")
                elif is_fixed_asset and not is_mapped_asset:
                    # Unmapped fixed assets: Stay in room (they're part of room furniture)
                    # Exception: If they were issued as rentals, they're already handled above
                    should_process_return = False
                    print(f"[CHECKOUT] Item {inv_item.name} is a FIXED ASSET (Unmapped) - will STAY in room")
                

                
                # CRITICAL: Only process stock movements for consumables and rentables
                # Fixed assets MUST stay in the room
                # CRITICAL: Process stock movements for ALL items (Consumables, Rentables, and Fixed Assets)
                # Fixed assets might stay in the room, but we still need to record damage/missing status.
                if inv_item:
                    
                    # Get current room stock for this item
                    # room_room is already fetched above
                    # Ensure we have the room and location
                    if room_room and room_room.inventory_location_id:
                        room_loc_id = room_room.inventory_location_id
                        
                        from app.models.inventory import LocationStock, InventoryTransaction, StockIssue, StockIssueDetail, Location
                        
                        room_stock_record = db.query(LocationStock).filter(
                            LocationStock.location_id == room_loc_id,
                            LocationStock.item_id == item.item_id
                        ).first()
                        
                        # STEP 1: Get quantities and validate
                        # CRITICAL FIX: Use provided allocated_stock to preserve split info (Rented vs Standard)
                        # room_stock_record.quantity is the TOTAL for that item ID, whereas item.allocated_stock is the share for this row.
                        allocated_stock = float(item.allocated_stock or 0.0)
                        if allocated_stock == 0 and room_stock_record:
                             # Fallback for old/generic payloads that don't send individual counts
                             allocated_stock = room_stock_record.quantity
                        
                        # CRITICAL: Identify fixed asset mapping quantity
                        from app.models.inventory import AssetMapping
                        mapped_asset_qty = db.query(func.sum(AssetMapping.quantity)).filter(
                            AssetMapping.location_id == room_loc_id,
                            AssetMapping.item_id == item.item_id,
                            AssetMapping.is_active == True
                        ).scalar() or 0.0
                        
                        # Only stock above the mapped quantity is "returnable" (Consumables/Issued Rentals)
                        returnable_pool = max(0, allocated_stock - mapped_asset_qty)
                        
                        # Add info to item_dict
                        item_dict['allocated_stock'] = allocated_stock
                        item_dict['mapped_asset_qty'] = mapped_asset_qty
                        item_dict['item_name'] = inv_item.name
                        item_dict['item_code'] = inv_item.item_code
                        item_dict['unit'] = inv_item.unit
                        
                        is_fixed_asset_local = item.is_fixed_asset or is_mapped_asset or getattr(inv_item, 'is_asset_fixed', False)
                        item_dict['is_fixed_asset'] = is_fixed_asset_local
                        
                        item_dict['is_rentable'] = item.is_rentable or is_rental
                        used_qty = item.used_qty or 0.0
                        missing_qty = item.missing_qty or 0.0
                        damage_qty = getattr(item, 'damage_qty', 0.0) or 0.0
                        
                        # Calculate how much of the RETURNABLE stock is unused
                        # used/missing/damage come out of returnable_pool first? 
                        # Usually, guest consumption/damage targets what was issued for them.
                        unused_from_pool = max(0, returnable_pool - used_qty - missing_qty - damage_qty)
                        
                        # If damage exceeds returnable pool, it hits the mapped assets
                        damage_to_assets = max(0, (used_qty + missing_qty + damage_qty) - returnable_pool)
                        
                        print(f"[CHECKOUT] Room {checkout_request.room_number} Item {inv_item.name}: Allocated={allocated_stock}, Mapped={mapped_asset_qty}, ReturnablePool={returnable_pool}, UnusedFromPool={unused_from_pool}, DamageToAssets={damage_to_assets}")
                        
                        # STEP 2: Execute room stock movements
                        if room_stock_record:
                            # NEW LOGIC: Deduct ONLY used and missing from room stock.
                            # Damaged items STAY in the room (as Damaged) and Unused items stay for next booking.
                            total_deduct = used_qty + missing_qty
                            if total_deduct > 0:
                                room_stock_record.quantity = max(0, room_stock_record.quantity - total_deduct)
                                room_stock_record.last_updated = datetime.utcnow()
                                print(f"[CHECKOUT] Deducted used/missing from room stock: {total_deduct} units. Remaining: {room_stock_record.quantity}")
                            
                            # STEP 3: Return Unused From Pool to Warehouse - DISABLED PER USER REQUEST
                            # "if the items are not returned in that step too, the items stay there in the room for next booking"
                            # if unused_from_pool > 0:
                            #     room_stock_record.quantity = max(0, room_stock_record.quantity - unused_from_pool)
                            #     print(f"[CHECKOUT] Returning unused issued stock to warehouse: {unused_from_pool} units. Remaining (Fixed): {room_stock_record.quantity}")
                            #     unused_qty = unused_from_pool
                            # else:
                            #     unused_qty = 0
                            unused_qty = 0 # No automatic return to warehouse at this step
                        else:
                            unused_qty = 0

                        # STEP 3: Return unused items to source location
                        if unused_qty > 0:
                            # Find source location to return unused items to (Warehouse)
                            source_loc_id = None
                            source_loc_name = "Warehouse"
                            
                            # 2a. Check if user specified a return location
                            if item.return_location_id:
                                user_loc = db.query(Location).filter(Location.id == item.return_location_id).first()
                                if user_loc:
                                     source_loc_id = user_loc.id
                                     source_loc_name = user_loc.name
                            
                            if not source_loc_id:
                                # Strategy 1: Find original source from last stock issue
                                last_issue = (db.query(StockIssue)
                                    .join(StockIssueDetail)
                                    .filter(
                                        StockIssue.destination_location_id == room_loc_id,
                                        StockIssueDetail.item_id == item.item_id
                                    )
                                    .order_by(StockIssue.issue_date.desc())
                                    .first()
                                )
                                if last_issue and last_issue.source_location_id:
                                    source_loc_id = last_issue.source_location_id
                            
                            # Last Fallback: Find any warehouse
                            if not source_loc_id:
                                fallback_loc = db.query(Location).filter(Location.location_type.in_(["WAREHOUSE", "CENTRAL_WAREHOUSE", "STORAGE"])).first()
                                if fallback_loc:
                                    source_loc_id = fallback_loc.id

                            if source_loc_id:
                                source_stock = db.query(LocationStock).filter(
                                    LocationStock.location_id == source_loc_id,
                                    LocationStock.item_id == item.item_id
                                ).first()
                                
                                if source_stock:
                                    source_stock.quantity += unused_qty
                                else:
                                    new_source_stock = LocationStock(
                                        location_id=source_loc_id,
                                        item_id=item.item_id,
                                        quantity=unused_qty,
                                        last_updated=datetime.utcnow()
                                    )
                                    db.add(new_source_stock)
                                    
                                # Record return transaction
                                return_txn = InventoryTransaction(
                                    item_id=item.item_id,
                                    transaction_type="transfer_in",
                                    quantity=unused_qty,
                                    unit_price=inv_item.unit_price,
                                    total_amount=unused_qty * (inv_item.unit_price or 0),
                                    reference_number=f"RET-RM{checkout_request.room_number}",
                                    notes=f"Stock return: Room {checkout_request.room_number} (Checkout #{checkout_request.id})",
                                    created_by=current_user.id
                                )
                                db.add(return_txn)
                                print(f"[CHECKOUT] Returned {unused_qty} units to {source_loc_id}")

                        # STEP 4: Deduct consumed items from GLOBAL stock
                        consumed_qty = used_qty + missing_qty + damage_qty
                        if consumed_qty > 0:
                            old_global_stock = inv_item.current_stock
                            inv_item.current_stock -= consumed_qty
                            print(f"[CHECKOUT] Deducted {consumed_qty} from global stock: {old_global_stock} → {inv_item.current_stock}")

                            # Adjustment: If item was consumed but had no room stock (e.g. Fixed Asset/Rentals unmapped),
                            # we ensure global stock still reduced. Room stock was updated above if record existed.
                            
                            # Separate Consumption (Used) vs Damage/Missing (Waste)
                            if used_qty > 0:
                                cons_txn = InventoryTransaction(
                                    item_id=item.item_id,
                                    transaction_type="out",
                                    quantity=used_qty,
                                    unit_price=inv_item.unit_price,
                                    total_amount=used_qty * (inv_item.unit_price or 0),
                                    reference_number=f"CONSUME-CHK-{checkout_request.id}",
                                    notes=f"Consumption at checkout - Room {checkout_request.room_number}",
                                    created_by=current_user.id
                                )
                                db.add(cons_txn)
                            
                            # Consumable Logic: Consolidate missing/damaged as Consumption to avoid confusing "Damaged" logs for soda/snacks
                            is_consumable = (not is_fixed_asset and not is_rental)
                            
                            bad_qty = missing_qty + damage_qty
                            if bad_qty > 0:
                                if is_consumable:
                                    # For consumables, just log as Consumption
                                    waste_txn = InventoryTransaction(
                                        item_id=item.item_id,
                                        transaction_type="out",
                                        quantity=bad_qty,
                                        unit_price=inv_item.unit_price,
                                        total_amount=bad_qty * (inv_item.unit_price or 0.0),
                                        reference_number=f"LOST-RM{checkout_request.room_number}",
                                        notes=f"Missing/Damaged consumable at checkout - Room {checkout_request.room_number}",
                                        created_by=current_user.id
                                    )
                                    db.add(waste_txn)
                                    print(f"[CHECKOUT] Logged {bad_qty} {inv_item.name} as consumption (Missing/Damaged consumable)")
                                else:
                                    # For Assets, still use WasteLog for maintenance tracking
                                    from app.models.inventory import WasteLog
                                    from app.curd.inventory import generate_waste_log_number
                                    
                                    waste_log_num = generate_waste_log_number(db)
                                    waste_log = WasteLog(
                                        log_number=waste_log_num,
                                        item_id=item.item_id,
                                        is_food_item=False,
                                        location_id=room_loc_id,
                                        quantity=bad_qty,
                                        unit=inv_item.unit,
                                        reason_code="Damaged/Missing",
                                        action_taken="Charged to Guest",
                                        notes=f"Checkout Room {checkout_request.room_number}",
                                        reported_by=current_user.id,
                                        waste_date=datetime.utcnow()
                                    )
                                    db.add(waste_log)
                                    db.flush()

                                    waste_txn = InventoryTransaction(
                                        item_id=item.item_id,
                                        transaction_type="waste_spoilage",
                                        quantity=bad_qty,
                                        unit_price=inv_item.unit_price,
                                        total_amount=bad_qty * (inv_item.unit_price or 0),
                                        reference_number=waste_log_num,
                                        notes=f"Damage/Missing at checkout - Room {checkout_request.room_number}",
                                        created_by=current_user.id
                                    )
                                    db.add(waste_txn)
                                    
                                    # NEW: Specially mark damaged items if they stay in room
                                    if damage_qty > 0:
                                        if getattr(item, 'is_rentable', False):
                                            # Mark the matching rental issue as damaged
                                            from sqlalchemy import or_
                                            rental_issue_to_mark = db.query(StockIssueDetail).join(StockIssue).filter(
                                                StockIssue.destination_location_id == room_loc_id,
                                                StockIssueDetail.item_id == item.item_id,
                                                or_(StockIssueDetail.rental_price > 0, StockIssueDetail.is_payable == True)
                                            ).order_by(StockIssue.issue_date.desc()).first()
                                            if rental_issue_to_mark:
                                                rental_issue_to_mark.is_damaged = True
                                                rental_issue_to_mark.damage_notes = f"Reported at checkout #{checkout_request.id}"
                                                db.add(rental_issue_to_mark)
                                                print(f"[CHECKOUT] Marked StockIssue as Damaged for {inv_item.name} (Rental) in Room {checkout_request.room_number}")
                                        else:
                                            # Use Registry for status
                                            from app.models.inventory import AssetRegistry
                                            registry_item = db.query(AssetRegistry).filter(
                                                AssetRegistry.item_id == item.item_id,
                                                AssetRegistry.current_location_id == room_loc_id
                                            ).first()
                                            if registry_item:
                                                registry_item.status = "damaged"
                                                db.add(registry_item)
                                            
                                            # Update mapping notes if it's a fixed asset mapping
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
                                                    print(f"[CHECKOUT] Marked Asset Mapping for {inv_item.name} as Damaged in Room {checkout_request.room_number}")
                                # Deactivate Asset Mapping ONLY if the mapped units themselves are damaged
                                if is_fixed_asset and room_stock_record and room_stock_record.quantity < mapped_asset_qty:
                                    # Deactivate just enough mappings to match the missing stock
                                    # Deactivate just enough mappings to match the missing stock
                                    mapping_to_deactivate = db.query(AssetMapping).filter(
                                        AssetMapping.location_id == room_loc_id,
                                        AssetMapping.item_id == item.item_id,
                                        AssetMapping.is_active == True
                                    ).first()

                                    if mapping_to_deactivate:
                                        if mapping_to_deactivate.quantity > 1:
                                            mapping_to_deactivate.quantity -= 1
                                            print(f"[CHECKOUT] Decremented Asset Mapping quantity for {inv_item.name} in Room {checkout_request.room_number}")
                                        else:
                                            mapping_to_deactivate.is_active = False
                                            print(f"[CHECKOUT] Deactivated Asset Mapping for {inv_item.name} in Room {checkout_request.room_number}")
                                        db.add(mapping_to_deactivate)


                        # --- CALCULATE VALID COMPLIMENTARY LIMIT FROM ISSUES ---
                        # We need to know how many "Complimentary" items were issued to this room during the stay.
                        # We scan StockIssueDetails for this room/booking.
                        
                        calculated_limit = 0
                        if checkout_request.booking_id:
                            booking = db.query(Booking).filter(Booking.id == checkout_request.booking_id).first()
                            if booking:
                                # Sum up issued quantity where is_payable is False (Complimentary)
                                # Filter by issue_date >= check_in to avoid counting previous guests' history
                                # Also filter by destination = room_loc_id
                                
                                comp_issued_qty = (db.query(func.sum(StockIssueDetail.issued_quantity))
                                    .join(StockIssue)
                                    .filter(
                                        StockIssue.destination_location_id == room_loc_id,
                                        StockIssueDetail.item_id == item.item_id,
                                        StockIssue.issue_date >= booking.check_in,
                                        or_(StockIssueDetail.is_payable == False, StockIssueDetail.is_payable == None)
                                    )
                                    .scalar()) or 0.0
                                
                                calculated_limit = float(comp_issued_qty)
                                print(f"[CHECKOUT] Found {calculated_limit} complimentary units issued for {inv_item.name} since {booking.check_in}")
                        else:
                            # Fallback if no booking ID (unlikely for occupied room, but safe fallback)
                            # Maybe use Master Data or 0? 
                            # User implies "assigned" limit matters. If we can't find assignment, use 0 or Master.
                            calculated_limit = float(inv_item.complimentary_limit or 0.0)

                        # Store this calculated limit in the item dict so billing logic sees it
                        item_dict['complimentary_limit'] = calculated_limit
                        limit = calculated_limit

                        # STEP 5: Calculate charges for used items using unified helper logic
                        if used_qty > 0:
                            # Limit is already calculated above as 'calculated_limit'
                            
                            # Use central helper for consistent calculation
                            usage_charge, price_to_use, actual_chargeable_qty = calculate_consumable_charge(inv_item, used_qty, limit_from_audit=limit)
                            
                            if usage_charge > 0:
                                item_dict['total_charge'] = item_dict.get('total_charge', 0) + usage_charge
                                item_dict['payable_usage_qty'] = actual_chargeable_qty
                                item_dict['unit_price'] = price_to_use 
                                print(f"[CHECKOUT] Applied usage charge for {inv_item.name}: {actual_chargeable_qty} x ₹{price_to_use}")
                            else:
                                # Item is complimentary or under limit
                                item_dict['total_charge'] = item_dict.get('total_charge', 0) + 0.0
                                item_dict['payable_usage_qty'] = 0.0
                                item_dict['unit_price'] = price_to_use
                                print(f"[CHECKOUT] {inv_item.name} is COMPLIMENTARY/under limit (Used: {used_qty}, Limit: {limit})")

                # --- CHARGE CALCULATION (Missing/Damage) ---
                # ALWAYS charge for missing/damaged items using the best available price + tax
                missing_qty = float(getattr(item, 'missing_qty', 0.0) or 0.0)
                damage_qty = float(getattr(item, 'damage_qty', 0.0) or 0.0)
                total_bad_qty = missing_qty + damage_qty
                
                if total_bad_qty > 0 and inv_item:
                    # Use selling price or cost+tax
                    price_base = float(inv_item.selling_price or inv_item.unit_price or 0.0)
                    if price_base > 0:
                        gst_rate = float(inv_item.gst_rate or 0.0)
                        # If using unit_price, we MUST add GST. If using selling_price, assume it's MRP (tax-incl).
                        # Actually, to be safe and consistent with the resort's expectations:
                        if inv_item.selling_price and inv_item.selling_price > 0:
                            unit_charge_with_tax = float(inv_item.selling_price)
                        else:
                            gst_multiplier = 1.0 + (gst_rate / 100.0)
                            unit_charge_with_tax = price_base * gst_multiplier
                        
                        total_charge = total_bad_qty * unit_charge_with_tax
                        
                        # Update item_dict for billing record
                        item_dict['missing_item_charge'] = total_charge
                        item_dict['damage_charge'] = total_charge 
                        item_dict['unit_price'] = unit_charge_with_tax
                        item_dict['damage_qty'] = damage_qty
                        item_dict['missing_qty'] = missing_qty
                        
                        total_missing_charges += total_charge
                        
                        # Add to summary details
                        missing_items_details.append({
                            "item_name": inv_item.name,
                            "item_code": inv_item.item_code,
                            "missing_qty": missing_qty,
                            "damage_qty": damage_qty,
                            "unit_price": unit_charge_with_tax,
                            "total_charge": total_charge,
                            "type": "damaged" if damage_qty > 0 else "missing"
                        })
                        print(f"[CHECKOUT] Applied {total_bad_qty} missing/damage charge for {inv_item.name}: ₹{total_charge}")

                # CRITICAL: Append the final fully-populated item_dict to the result list
                inventory_data_with_charges.append(item_dict)
    except Exception as e:
        print(f"[CHECKOUT CRASH] Error processing items: {traceback.format_exc()}")
        raise e

    
    # Process asset damages
    if payload.asset_damages:
        from app.models.inventory import AssetRegistry, WasteLog, InventoryTransaction, LocationStock
        from app.curd.inventory import generate_waste_log_number
        
        # Determine room object once
        room_obj = db.query(Room).filter(Room.number == checkout_request.room_number).first()
        
        for asset in payload.asset_damages:
            asset_dict = asset.dict()
            # Asset damage is always charged
            asset_charge = asset.replacement_cost
            total_missing_charges += asset_charge
            
            asset_dict['missing_item_charge'] = asset_charge
            asset_dict['unit_price'] = asset.replacement_cost
            asset_dict['missing_qty'] = 1  # Treat as 1 unit damaged
            asset_dict['is_fixed_asset'] = True
            
            missing_items_details.append({
                "item_name": asset.item_name,
                "item_code": "ASSET",
                "missing_qty": 1,
                "unit_price": asset.replacement_cost,
                "total_charge": asset_charge,
                "is_fixed_asset": True,
                "notes": asset.notes
            })
            
            inventory_data_with_charges.append(asset_dict) 
            
            # Find the Asset Registry Record
            asset_registry_id = getattr(asset, 'asset_registry_id', None)
            item_id = getattr(asset, 'item_id', None)
            
            asset_record = None
            if asset_registry_id:
                asset_record = db.query(AssetRegistry).filter(AssetRegistry.id == asset_registry_id).first()
            elif item_id and room_obj and room_obj.inventory_location_id:
                asset_record = db.query(AssetRegistry).filter(
                    AssetRegistry.item_id == item_id,
                    AssetRegistry.current_location_id == room_obj.inventory_location_id,
                    AssetRegistry.status == "active"
                ).first()
            
            # Fallback vars
            target_item_id = None
            target_location_id = None
            
            if asset_record:
                # 1. Update Asset Status if registry exists
                asset_record.status = "damaged"
                asset_record.notes = f"Damaged during checkout. {asset.notes or ''}"
                print(f"[CHECKOUT] Updated AssetRegistry ID {asset_record.id} status to 'damaged'")
                
                target_item_id = asset_record.item_id
                target_location_id = asset_record.current_location_id
            
            elif item_id and room_obj and room_obj.inventory_location_id:
                # Fallback: Untracked/Generic Asset in Room
                print(f"[CHECKOUT] AssetRegistry not found for item {item_id}. Processing as generic asset damage.")
                target_item_id = item_id
                target_location_id = room_obj.inventory_location_id
                
            if target_item_id and target_location_id:
                # Determine if it's actually an asset or a consumable
                t_item = db.query(InventoryItem).filter(InventoryItem.id == target_item_id).first()
                is_actually_asset = t_item.is_asset_fixed if t_item else True
                
                if is_actually_asset:
                    # 2. Create Waste Log (Maintenance track for assets)
                    waste_log_num = generate_waste_log_number(db)
                    waste_log = WasteLog(
                        log_number=waste_log_num,
                        item_id=target_item_id,
                        is_food_item=False,
                        location_id=target_location_id,
                        quantity=1,
                        unit="pcs",
                        reason_code="Damaged",
                        action_taken="Charged to Guest",
                        notes=f"Damaged asset during checkout - Room {checkout_request.room_number}. {asset.notes or ''}",
                        reported_by=current_user.id,
                        waste_date=datetime.utcnow()
                    )
                    db.add(waste_log)
                    db.flush() # Ensure visible for next ID generation
                    print(f"[CHECKOUT] Created waste log {waste_log_num} for damaged asset")
                    
                    # Fetch unit price for transaction
                    unit_price = 0
                    if t_item: unit_price = t_item.unit_price or 0

                    # 3. Create Damage Transaction (Waste type for assets)
                    damage_txn = InventoryTransaction(
                        item_id=target_item_id,
                        transaction_type="waste",
                        quantity=1,
                        unit_price=unit_price,
                        total_amount=asset.replacement_cost,
                        reference_number=waste_log_num,
                        notes=f"WASTE: Damaged asset at checkout - Room {checkout_request.room_number}",
                        created_by=current_user.id
                    )
                    db.add(damage_txn)
                else:
                    # It's a consumable reported as asset damage (Safety fallback)
                    # Just log as consumption
                    damage_txn = InventoryTransaction(
                        item_id=target_item_id,
                        transaction_type="waste",
                        quantity=1,
                        unit_price=t_item.unit_price if t_item else 0,
                        total_amount=asset.replacement_cost,
                        reference_number=f"LOST-DAM-{checkout_request.id}",
                        notes=f"WASTE: Damaged item at checkout - Room {checkout_request.room_number}",
                        created_by=current_user.id
                    )
                    db.add(damage_txn)
                    print(f"[CHECKOUT] Logged damaged consumable {t_item.name if t_item else ''} as waste")
                print(f"[CHECKOUT] Created damage transaction for asset")
                
                # 4. Deduct LocationStock (The Fix)
                loc_stock = db.query(LocationStock).filter(
                    LocationStock.location_id == target_location_id,
                    LocationStock.item_id == target_item_id
                ).first()
                if loc_stock:
                    loc_stock.quantity = max(0, loc_stock.quantity - 1)
                    loc_stock.last_updated = datetime.utcnow()
                    print(f"[CHECKOUT] Deducted LocationStock for damaged asset: {loc_stock.quantity + 1} -> {loc_stock.quantity}")

                # 4b. Deactivate Asset Mapping (DISABLED - User wants persistence until completion)
                # from app.models.inventory import AssetMapping
                # db.query(AssetMapping).filter(
                #    AssetMapping.location_id == target_location_id,
                #    AssetMapping.item_id == target_item_id
                # ).update({"is_active": False})
                print(f"[CHECKOUT] Deactivated Asset Mapping for damaged asset {target_item_id}")

                # 5. Deduct Global Stock (New Fix)
                inv_item_obj = db.query(InventoryItem).filter(InventoryItem.id == target_item_id).first()
                if inv_item_obj:
                    inv_item_obj.current_stock -= 1
                    print(f"[CHECKOUT] Deducted Global Stock for damaged asset {inv_item_obj.name}: {inv_item_obj.current_stock + 1} -> {inv_item_obj.current_stock}")

    if inventory_data_with_charges:
        checkout_request.inventory_data = inventory_data_with_charges
    else:
        # Ensure inventory_data is at least an empty list, not None
        checkout_request.inventory_data = []
        
    checkout_request.status = "completed"
    checkout_request.completed_at = datetime.utcnow()
    
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
def get_pre_checkout_verification_data(room_number: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get pre-checkout verification data for a room:
    - Room status
    - Actual Consumables stock in room (from LocationStock)
    - Actual Fixed Assets in room (from AssetRegistry) with serial numbers
    """
    room = db.query(Room).filter(Room.number == room_number).first()
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
        from app.models.inventory import InventoryItem, LocationStock, AssetRegistry, InventoryCategory
        
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
                "current_stock": 1 # It's a single unit
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


@router.get("/checkouts", response_model=List[CheckoutFull])
def get_all_checkouts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), skip: int = 0, limit: int = 20):
    """Retrieves a list of all completed checkouts, ordered by most recent - optimized for low network"""
    from app.utils.api_optimization import optimize_limit, MAX_LIMIT_LOW_NETWORK
    limit = optimize_limit(limit, MAX_LIMIT_LOW_NETWORK)
    checkouts = db.query(Checkout).order_by(Checkout.id.desc()).offset(skip).limit(limit).all()
    print(f"DEBUG: get_all_checkouts - Found {len(checkouts)} checkouts")
    return checkouts if checkouts else []

@router.post("/cleanup-orphaned-checkouts")
def cleanup_orphaned_checkouts_endpoint(
    room_number: Optional[str] = Query(None),
    booking_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
            room = db.query(Room).filter(Room.number == room_number).first()
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
def repair_room_checkout_status(room_number: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Repair function to fix mismatched checkout status.
    If a checkout record exists but room is not marked as Available, fix the room status.
    If room is Available but no checkout record exists, create a minimal checkout record.
    """
    room = db.query(Room).filter(Room.number == room_number).first()
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
                        InventoryItem.is_fixed_asset == False
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
                                        last_updated=datetime.utcnow()
                                    ))
                                
                                db.add(InventoryTransaction(
                                    item_id=item_stock.item_id,
                                    transaction_type="transfer_out",
                                    quantity=-qty,
                                    notes=f"Checkout cleanup - returned from Room {room.number} to {target_location.name}",
                                    created_by=current_user.id if current_user else None
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

    return {
        "id": checkout.id,
        "booking_id": checkout.booking_id,
        "package_booking_id": checkout.package_booking_id,
        "room_total": checkout.room_total,
        "food_total": final_food_total,
        "service_total": final_service_total,
        "package_total": checkout.package_total,
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
        "bill_details": bill_details
    }

@router.get("/active-rooms", response_model=List[dict])
def get_active_rooms(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), skip: int = 0, limit: int = 20):
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
        active_bookings = db.query(Booking).options(
            joinedload(Booking.booking_rooms).joinedload(BookingRoom.room)
        ).filter(
            func.lower(Booking.status).in_(['checked-in', 'checked_in', 'checked in'])
        ).all()
        
        active_package_bookings = db.query(PackageBooking).options(
            joinedload(PackageBooking.rooms).joinedload(PackageBookingRoom.room)
        ).filter(
            func.lower(PackageBooking.status).in_(['checked-in', 'checked_in', 'checked in'])
        ).all()
        
        result = []
        
        # Debug: Log what we found
        print(f"[DEBUG active-rooms] Found {len(active_bookings)} regular bookings and {len(active_package_bookings)} package bookings")
        for b in active_bookings[:5]:  # Log first 5 to avoid spam
            print(f"[DEBUG] Booking {b.id}: status='{b.status}', rooms={len(b.booking_rooms)}")
            for br in b.booking_rooms[:3]:  # Log first 3 rooms per booking
                if br.room:
                    print(f"[DEBUG]   Room {br.room.number}: status='{br.room.status}'")
        
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
                    print(f"[DEBUG active-rooms] Repairing room {link.room.number}: status was 'Available', setting to 'Checked-in' (booking {booking.id} is checked-in)")
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
                    print(f"[DEBUG active-rooms] Repairing room {link.room.number}: status was 'Available', setting to 'Checked-in' (package booking {pkg_booking.id} is checked-in)")
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
        print(f"[DEBUG active-rooms] Final result: {len(result)} room options")
        if len(result) == 0:
            print("[DEBUG active-rooms] WARNING: No rooms found! Possible reasons:")
            print(f"  - No bookings with status 'checked-in' or 'checked_in'")
            print(f"  - All rooms in checked-in bookings have status 'Available' (already checked out)")
            print(f"  - Room status values don't match expected format")
        
        return result[skip:skip+limit]
    except Exception as e:
        # Return empty list on error to prevent 500 response
        import traceback
        print(f"[ERROR active-rooms] Exception: {str(e)}")
        print(traceback.format_exc())
        return []

def _calculate_bill_for_single_room(db: Session, room_number: str):
    """
    Calculates bill for a single room only, regardless of how many rooms are in the booking.
    """
    # 1. Find the room
    room = db.query(Room).filter(Room.number == room_number).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found.")
    
    # 2. Find the active parent booking (regular or package) linked to this room
    booking, is_package = None, False
    
    booking_link = (db.query(BookingRoom)
                    .join(Booking)
                    .options(joinedload(BookingRoom.booking))
                    .filter(BookingRoom.room_id == room.id, Booking.status.in_(['checked-in', 'checked_in', 'booked']))
                    .order_by(Booking.id.desc()).first())
    
    # Fallback: Check for recently checked out booking if no active booking found
    if not booking_link:
        booking_link = (db.query(BookingRoom)
                        .join(Booking)
                        .options(joinedload(BookingRoom.booking))
                        .filter(BookingRoom.room_id == room.id, Booking.status.in_(['checked-out', 'checked_out', 'checked out']))
                        .order_by(Booking.id.desc()).first())

    if booking_link:
        booking = booking_link.booking
        if booking.status not in ['checked-in', 'checked_in', 'booked', 'checked-out', 'checked_out', 'checked out']:
            raise HTTPException(status_code=400, detail=f"Booking is not in a valid state for checkout. Current status: {booking.status}")
    else:
        package_link = (db.query(PackageBookingRoom)
                        .join(PackageBooking)
                        .options(joinedload(PackageBookingRoom.package_booking))
                        .filter(PackageBookingRoom.room_id == room.id, PackageBooking.status.in_(['checked-in', 'checked_in', 'booked']))
                        .order_by(PackageBooking.id.desc()).first())
        
        # Fallback for package
        if not package_link:
            package_link = (db.query(PackageBookingRoom)
                            .join(PackageBooking)
                            .options(joinedload(PackageBookingRoom.package_booking))
                            .filter(PackageBookingRoom.room_id == room.id, PackageBooking.status.in_(['checked-out', 'checked_out', 'checked out']))
                            .order_by(PackageBooking.id.desc()).first())
                            
        if package_link:
            booking = package_link.package_booking
            is_package = True
            if booking.status not in ['checked-in', 'checked_in', 'booked', 'checked-out', 'checked_out', 'checked out']:
                raise HTTPException(status_code=400, detail=f"Package booking is not in a valid state for checkout. Current status: {booking.status}")
    
    if not booking:
        raise HTTPException(status_code=404, detail=f"No active booking found for room {room_number}.")
    
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
        # For regular bookings: calculate room charges as days * room price
        charges.room_charges = (room.price or 0) * stay_days
    
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
    
    # if last_checkout and last_checkout.checkout_date:
    #     # If last checkout was after the calculated start time, use it as the new start time
    #     # This handles cases where previous guest checked out on the same day as new guest check-in
    #     if last_checkout.checkout_date > check_in_datetime:
    #         check_in_datetime = last_checkout.checkout_date
    #         print(f"[DEBUG] Adjusted check-in datetime based on previous checkout: {check_in_datetime}")
            
    print(f"[DEBUG] Using billing start time: {check_in_datetime}")

    # Get food and service charges for THIS ROOM ONLY, filtered by check-in datetime
    # Include ALL food orders (both billed and unbilled) - show paid ones with zero amount
    all_food_order_items = (db.query(FoodOrderItem)
                           .join(FoodOrder)
                           .options(joinedload(FoodOrderItem.food_item), joinedload(FoodOrderItem.order))
                           .filter(
                               FoodOrder.room_id == room.id,
                               FoodOrder.created_at >= check_in_datetime
                           )
                           .all())
    
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
    all_assigned_services = db.query(AssignedService).options(joinedload(AssignedService.service)).filter(
        AssignedService.room_id == room.id
    ).all()
    
    # Separate unbilled and billed services
    unbilled_services = [ass for ass in all_assigned_services if ass.billing_status == "unbilled"]
    billed_services = [ass for ass in all_assigned_services if ass.billing_status == "billed"]
    
    # Calculate charges: only unbilled items contribute to charges
    charges.food_charges = sum(
        (item.quantity * item.food_item.price) 
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
                    "complimentary_qty": 0.0
                }
            
            # OR logic for fixed flag within this specific (iid, is_rent) group
            if is_fixed: aggregated_audit[audit_key]["is_fixed_asset"] = True
            
            # Combine quantities
            aggregated_audit[audit_key]["used_qty"] += float(item_data.get('used_qty') or 0)
            aggregated_audit[audit_key]["damage_qty"] += float(item_data.get('damage_qty') or 0)
            aggregated_audit[audit_key]["missing_qty"] += float(item_data.get('missing_qty') or 0)
            aggregated_audit[audit_key]["provided_bad_charge"] += float(item_data.get('damage_charge') or item_data.get('missing_item_charge') or item_data.get('total_charge') or 0)
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
        
        if item_gst == 0 and is_known_asset:
            item_gst = 12.0 # Standard fallback for assets to avoid tax-exclusive prices
            
        pur_price_with_gst = float(inv_item.unit_price or 0.0) * (1.0 + item_gst / 100.0)
        replacement_price = pur_price_with_gst if pur_price_with_gst > 0 else (selling_price * (1.12 if selling_price > 0 else 1.0))
        
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
        
        if used_qty > 0 or allocated_stock > 0 or missing_qty > 0:
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
            
            if is_rentable:
                # Rent for rentals: Usually no complimentary limit applies to explicit rentals
                # unless they were flagged as such in the audit.
                total_audited_qty = max(used_qty, allocated_stock)
                
                # If it's a rental batch from audit, we ignore the master-data default limit
                # because rentals are explicitly billed items.
                actual_limit = limit if item_data.get('complimentary_qty', 0) > 0 else 0.0
                payable_qty = max(0, total_audited_qty - actual_limit)
                
                if rental_unit_price > 0:
                    usage_charge = payable_qty * rental_unit_price
                else:
                    usage_charge = 0.0

            elif is_amenity or (getattr(inv_item, 'is_sellable_to_guest', False) or limit > 0):
                # Consumables / Amenities
                total_consumed = used_qty 
                # CHANGE: Do NOT cap consumables by allocated stock if reported as used
                # because system stock might be out of sync with physical presence.
                # if allocated_stock > 0:
                #      total_consumed = min(total_consumed, allocated_stock)
                
                usage_charge, replacement_price, chargeable_qty = calculate_consumable_charge(inv_item, total_consumed, limit_from_audit=limit)
                # Since missing is handled in usage_charge for these items, we zero it out to prevent double-charging in bad_charge logic
                missing_qty = 0 


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
             # print(f"[BILLING FIX] Forced bad_charge calculation for {inv_item.name}: {bad_charge}")

        total_item_charge = usage_charge + bad_charge
        
        if is_rentable or is_fixed_asset:
            # Asset / Rental Visibility
            display_qty = max(used_qty, allocated_stock)
            
            # Note for guest if rent is waived or if it's a stay-related asset
            item_notes = "Stay-related"
            if is_rentable:
                item_notes = "Rental"
                if (damage_qty + missing_qty) > 0 and usage_charge == 0:
                    item_notes = "Rent waived (Damaged/Missing)"
            
            # Visibility logic: Only Rentable items should appear in the Usage section.
            # Fixed assets (non-rentable) appear only in Asset Damages if they are damaged.
            if is_rentable:
                charges.inventory_usage.append({
                    "date": checkout_request.completed_at or datetime.now(),
                    "item_name": clean_name,
                    "category": inv_item.category.name if inv_item.category else ("Rental" if is_rentable else "Asset"),
                    "quantity": display_qty,
                    "unit": inv_item.unit or "pcs",
                    "rental_price": rental_unit_price if is_rentable else 0.0,
                    "rental_charge": usage_charge,
                    "is_rental": is_rentable,
                    "is_payable": True, # Ensure it shows up on the bill list
                    "notes": item_notes
                })
                # Add to total rental charges
                if usage_charge > 0:
                    charges.inventory_charges = (charges.inventory_charges or 0) + usage_charge

        if is_fixed_asset:
            # Pure Fixed Asset Logic
            # USER REQUEST: Pure fixed assets (not rented) should NOT be shown in bill if they are OK
            if (damage_qty + missing_qty) > 0:
                charges.fixed_assets.append({
                    "item_name": clean_name,
                    "status": "Damaged" if damage_qty > 0 else "Missing",
                    "quantity": damage_qty + missing_qty,
                    "notes": f"Verified from audit"
                })
            # Also keep it in internal records if needed, but for the bill, we follow the request.
            # Fixed assets are NOT added to inventory_usage unless they are rentable.

            # Add to Asset Damages if there is damage OR if there is a bad_charge (manual charge)
            if bad_charge > 0 or damage_qty > 0 or missing_qty > 0:
                final_bad_charge = bad_charge
                # Safety net: If bad_charge is 0 but we have damage, use replacement_price
                if final_bad_charge == 0:
                    # Fallback price logic: Try 1.5x Unit Price if replacement_price is 0
                    safe_price = replacement_price
                    if safe_price == 0:
                         safe_price = float(inv_item.unit_price or 0) * 1.5
                    
                    if safe_price == 0: safe_price = 50.0 # Standard fallback for small assets
                    
                    final_bad_charge = (damage_qty + missing_qty) * safe_price
                    print(f"[BILLING_FIX] Used fallback price {safe_price} for {inv_item.name} damage")

                if final_bad_charge > 0:
                    charges.asset_damage_charges = (charges.asset_damage_charges or 0) + final_bad_charge
                    label_suffix = " (Damaged)" if damage_qty > 0 else " (Missing)"
                    if damage_qty > 0 and missing_qty > 0: label_suffix = " (Damaged/Missing)"
                    charges.asset_damages.append({
                        "item_name": f"{clean_name}{label_suffix}",
                        "replacement_cost": final_bad_charge,
                        "notes": f"Damaged: {damage_qty}, Missing: {missing_qty}"
                    })
        else:
            # Consumables Display
            # CHANGE: Only add to consumables if it's NOT an asset category item
            # items like "Bath towel" even if marked sellable should stay in Assets/Rentals
            if is_asset_category:
                pass # Already handled above in fixed_assets or inventory_usage
            else:
                # For Consumables, we rely ONLY on used_qty to match billing calculation
                total_qty = used_qty 
                if allocated_stock > 0:
                    total_qty = min(used_qty, allocated_stock)
                
                if total_qty > 0 or total_item_charge > 0:
                    label = clean_name
                    # Only show breakdown if there's actual damage
                    if damage_qty > 0:
                        label += f" ({int(total_qty - damage_qty)} Used, {int(damage_qty)} Damaged)"
                    
                    charges.consumables_charges = (charges.consumables_charges or 0) + total_item_charge
                    charges.consumables_items.append({
                        "date": checkout_request.completed_at or datetime.now(), # Added date for separator compatibility
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
    stock_issues = (db.query(StockIssue)
                    .options(joinedload(StockIssue.details).joinedload(StockIssueDetail.item))
                    .filter(StockIssue.destination_location_id == room.inventory_location_id,
                            StockIssue.issue_date >= check_in_datetime)
                    .all())
    
    for issue in stock_issues:

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
                u_charge = r_price * detail.issued_quantity
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

def _calculate_bill_for_entire_booking(db: Session, room_number: str):
    """
    Core logic: Finds an entire booking from a single room number and calculates the total bill
    for all associated rooms and services.
    """
    # 1. Find the initial room to identify the parent booking
    initial_room = db.query(Room).filter(Room.number == room_number).first()
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

    # Fallback: Check for recently checked out booking
    if not booking_link:
        booking_link = (db.query(BookingRoom)
                        .join(Booking)
                        .options(joinedload(BookingRoom.booking))
                        .filter(BookingRoom.room_id == initial_room.id, Booking.status.in_(['checked-out', 'checked_out', 'checked out']))
                        .order_by(Booking.id.desc()).first())

    if booking_link:
        booking = booking_link.booking
        # Validate booking status before proceeding
        if booking.status not in ['checked-in', 'checked_in', 'booked', 'checked-out', 'checked_out', 'checked out']:
            raise HTTPException(status_code=400, detail=f"Booking is not in a valid state for checkout. Current status: {booking.status}")
    else:
        package_link = (db.query(PackageBookingRoom)
                        .join(PackageBooking)
                        .options(joinedload(PackageBookingRoom.package_booking)) # Eager load the booking
                        .filter(PackageBookingRoom.room_id == initial_room.id, PackageBooking.status.in_(['checked-in', 'checked_in', 'booked']))
                        .order_by(PackageBooking.id.desc()).first())
        
        # Fallback for package
        if not package_link:
            package_link = (db.query(PackageBookingRoom)
                            .join(PackageBooking)
                            .options(joinedload(PackageBookingRoom.package_booking))
                            .filter(PackageBookingRoom.room_id == initial_room.id, PackageBooking.status.in_(['checked-out', 'checked_out', 'checked out']))
                            .order_by(PackageBooking.id.desc()).first())

        if package_link:
            booking = package_link.package_booking
            is_package = True
            # Validate booking status before proceeding
            if booking.status not in ['checked-in', 'checked_in', 'booked', 'checked-out', 'checked_out', 'checked out']:
                raise HTTPException(status_code=400, detail=f"Package booking is not in a valid state for checkout. Current status: {booking.status}")

    if not booking:
        raise HTTPException(status_code=404, detail=f"No active booking found for room {room_number}.")

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
        # For regular bookings: calculate room charges as number of rooms * days * room price
        charges.room_charges = sum((room.price or 0) * stay_days for room in all_rooms)
    
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
    
    # if last_checkout and last_checkout.checkout_date:
    #     if last_checkout.checkout_date > check_in_datetime:
    #         check_in_datetime = last_checkout.checkout_date
    #         print(f"[DEBUG] Adjusted check-in datetime based on previous checkout: {check_in_datetime}")
            
    print(f"[DEBUG] Using billing start time: {check_in_datetime}")

    # Sum up additional food and service charges from all rooms
    # Include ALL food orders (both billed and unbilled) - show paid ones with zero amount
    all_food_order_items = (db.query(FoodOrderItem)
                           .join(FoodOrder)
                           .options(joinedload(FoodOrderItem.food_item), joinedload(FoodOrderItem.order))
                           .filter(
                               FoodOrder.room_id.in_(room_ids),
                               FoodOrder.created_at >= check_in_datetime
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

    # Get ALL assigned services for these rooms (both billed and unbilled)
    all_assigned_services = db.query(AssignedService).options(joinedload(AssignedService.service)).filter(
        AssignedService.room_id.in_(room_ids)
    ).all()
    
    # Separate unbilled and billed services
    unbilled_services = [ass for ass in all_assigned_services if ass.billing_status == "unbilled"]
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
    
    for ass in billed_services:
        charges.service_items.append({
            "service_name": ass.service.name,
            "charges": 0.0
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
            
            # Master Prices
            selling_price = float(inv_item.selling_price or 0.0)
            replacement_price = selling_price if selling_price > 0 else (float(inv_item.unit_price or 0.0) * (1.0 + float(inv_item.gst_rate or 0.0) / 100.0))
            
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
            rental_unit_price = rm.get("rental_price", 0) or (selling_price if is_rentable else 0)
            
            if used_qty > 0 or allocated_stock > 0:
                limit = inv_item.complimentary_limit or 0
                if is_rentable:
                    # Apply rent to all audited units, even if damaged or lost.
                    total_audited_qty = max(used_qty, allocated_stock)
                    
                    # Bypass master-data limit for explicit rentals from audit
                    audit_limit = float(item_data.get('complimentary_qty') or item_data.get('complimentary_limit') or 0.0)
                    actual_limit = audit_limit if audit_limit > 0 else 0.0
                    
                    payable_qty = max(0, total_audited_qty - actual_limit)
                    usage_charge = payable_qty * rental_unit_price
                
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
def get_bill_for_booking(room_number: str, checkout_mode: str = "multiple", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Returns a bill summary for the booking associated with the given room number.
    If checkout_mode is 'single', calculates bill for that room only.
    If checkout_mode is 'multiple', calculates bill for all rooms in the booking.
    """
    if checkout_mode == "single":
        bill_data = _calculate_bill_for_single_room(db, room_number)
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
        bill_data = _calculate_bill_for_entire_booking(db, room_number)
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
def process_booking_checkout(room_number: str, request: CheckoutRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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
    room = db.query(Room).filter(Room.number == room_number).first()
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
            # Check for checkout request
            checkout_request = None
            if is_package:
                checkout_request = db.query(CheckoutRequestModel).filter(
                    CheckoutRequestModel.package_booking_id == booking.id,
                    CheckoutRequestModel.status.in_(["pending", "inventory_checked"])
                ).order_by(CheckoutRequestModel.id.desc()).first()
            else:
                checkout_request = db.query(CheckoutRequestModel).filter(
                    CheckoutRequestModel.booking_id == booking.id,
                    CheckoutRequestModel.status.in_(["pending", "inventory_checked"])
                ).order_by(CheckoutRequestModel.id.desc()).first()
            
            # Block checkout if inventory is not checked
            if checkout_request and checkout_request.status == "pending" and not checkout_request.inventory_checked:
                raise HTTPException(
                    status_code=400, 
                    detail="Inventory must be checked before completing checkout. Please verify room inventory first."
                )
    
    if checkout_mode == "single":
        # Single room checkout
        # Calculate bill first - this will validate that there's an active booking
        bill_data = _calculate_bill_for_single_room(db, room_number)
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
                Checkout.room_number == room_number
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
                bill_details=bill_details_data  # Store the detailed bill
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
                    create_checkout_verification(db, new_checkout.id, room_verification, room.id)
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
                    
                    create_checkout_verification(db, new_checkout.id, room_ver_data, room.id)
            
            # 10. Process split payments
            if request.split_payments:
                process_split_payments(db, new_checkout.id, request.split_payments)
            elif request.payment_method:
                # Legacy single payment method
                payment_record = CheckoutPayment(
                    checkout_id=new_checkout.id,
                    payment_method=request.payment_method,
                    amount=grand_total,
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
                        new_checkout.id, current_user.id if current_user else None
                    )

            # Clear remaining consumables from room inventory
            # Clear remaining consumables from room inventory - REMOVED
            # This logic was incorrectly setting GLOBAL stock to 0. Use proper transfer logic if needed.
            # room_items = ... (Removed)
            
            # Trigger linen cycle (move bed sheets/towels to laundry)
            trigger_linen_cycle(db, room.id, new_checkout.id)
            
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
            #             InventoryItem.is_fixed_asset == False
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
                    db, room.id, room.number, booking.guest_name
                )
                # Create refill service request with checkout_id to get consumables data
                service_request_crud.create_refill_service_request(
                    db, room.id, room.number, booking.guest_name, new_checkout.id
                )
                # Create return items service request for unused items
                service_request_crud.create_return_items_service_request(
                    db, room.id, room.number, booking.guest_name, new_checkout.id
                )
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
                    service_total=float(new_checkout.service_total or 0),
                    package_total=float(new_checkout.package_total or 0),
                    tax_amount=float(new_checkout.tax_amount or 0),
                    discount_amount=float(new_checkout.discount_amount or 0),
                    grand_total=float(new_checkout.grand_total or 0),
                    guest_name=new_checkout.guest_name or "Guest",
                    room_number=new_checkout.room_number or room_number,
                    gst_rate=18.0,  # Default, can be calculated from tax_amount
                    payment_method=payment_method,
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
        bill_data = _calculate_bill_for_entire_booking(db, room_number)

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
            subtotal = charges.total_due + total_consumables_charges + total_asset_damage_charges + total_key_card_fee + late_checkout_fee
            
            # Recalculate GST
            consumables_gst = total_consumables_charges * 0.05
            asset_damage_gst = 0.0 # No GST on asset damages as per request
            
            tax_amount = (charges.total_gst or 0) + consumables_gst + asset_damage_gst
            
            discount_amount = max(0, request.discount_amount or 0)
            tips_gratuity = max(0, request.tips_gratuity or 0.0)
            
            grand_total_before_advance = max(0, subtotal + tax_amount - discount_amount + tips_gratuity)
            grand_total = max(0, grand_total_before_advance - advance_deposit)
            
            # 5. Get effective checkout date
            effective_checkout = bill_data.get("effective_checkout_date", booking.check_out)
            effective_checkout_datetime = datetime.combine(effective_checkout, datetime.min.time())
            
            # 6. Generate invoice number
            invoice_number = generate_invoice_number(db)
            
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
                bill_details=bill_details_data
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
                        # Deduct consumables
                        deduct_room_consumables(
                            db, room_obj.id, room_verification.consumables, 
                            new_checkout.id, current_user.id if current_user else None
                        )
            
            # Deduct from CheckoutRequest if available
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
                process_split_payments(db, new_checkout.id, request.split_payments)
            elif request.payment_method:
                payment_record = CheckoutPayment(
                    checkout_id=new_checkout.id,
                    payment_method=request.payment_method,
                    amount=grand_total,
                    notes="Single payment method"
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
            
            # 11. Inventory Triggers for all rooms
            if request.room_verifications:
                for room_verification in request.room_verifications:
                    room_obj = next((r for r in all_rooms if r.number == room_verification.room_number), None)
                    if room_obj:
                        deduct_room_consumables(
                            db, room_obj.id, room_verification.consumables,
                            new_checkout.id, current_user.id if current_user else None
                        )
                        trigger_linen_cycle(db, room_obj.id, new_checkout.id)
            
            # 12. Update booking and room statuses
            booking.status = "checked_out"
            booking.total_amount = grand_total
            db.query(Room).filter(Room.id.in_(room_ids)).update({"status": "Available"})
            
            # 12.5. Automatically create cleaning and refill service requests for all rooms
            try:
                from app.curd import service_request as service_request_crud
                for room in all_rooms:
                    try:
                        # Create cleaning service request
                        service_request_crud.create_cleaning_service_request(
                            db, room.id, room.number, booking.guest_name
                        )
                        # Create refill service request with checkout_id to get consumables data
                        service_request_crud.create_refill_service_request(
                            db, room.id, room.number, booking.guest_name, new_checkout.id
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
                        service_total=float(new_checkout.service_total or 0),
                        package_total=float(new_checkout.package_total or 0),
                        tax_amount=float(new_checkout.tax_amount or 0),
                        discount_amount=float(new_checkout.discount_amount or 0),
                        grand_total=float(new_checkout.grand_total or 0),
                        guest_name=new_checkout.guest_name or "Guest",
                        room_number=room_number,  # Primary room number
                        gst_rate=18.0,
                        payment_method=payment_method,
                        created_by=current_user.id if current_user else None,
                        advance_amount=float(new_checkout.advance_deposit or 0)
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
                    detail=f"This booking has already been checked out. A checkout record already exists for this booking."
                )
            raise HTTPException(status_code=500, detail=f"Checkout failed due to an internal error: {error_detail}")

        # Return the data from the newly created checkout record
        return CheckoutSuccess(
            checkout_id=new_checkout.id,
            grand_total=new_checkout.grand_total,
            checkout_date=new_checkout.checkout_date or new_checkout.created_at
        )
