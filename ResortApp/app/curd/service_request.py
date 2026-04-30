from sqlalchemy.orm import Session, joinedload
from app.models.service_request import ServiceRequest
from app.models.foodorder import FoodOrder, FoodOrderItem
from app.models.room import Room
from app.models.employee import Employee
from app.schemas.service_request import ServiceRequestCreate, ServiceRequestUpdate
from typing import List, Optional
from datetime import timezone, datetime
from app.curd.notification import notify_service_request_created, notify_service_request_status_changed

def create_service_request(db: Session, request_data: ServiceRequestCreate, branch_id: int = 1):
    request = ServiceRequest(
        food_order_id=request_data.food_order_id,
        room_id=request_data.room_id,
        employee_id=request_data.employee_id,
        request_type=request_data.request_type,
        description=request_data.description,
        image_path=request_data.image_path,
        status="pending",
        branch_id=branch_id
    )

    db.add(request)
    db.commit()
    db.refresh(request)
    
    # Notify about new service request
    try:
        room = db.query(Room).filter(Room.id == request.room_id, Room.branch_id == branch_id).first()
        room_number = room.number if room else "Unknown"
        notify_service_request_created(db, request.request_type, room_number, request.id, branch_id=branch_id)
    except Exception as e:
        print(f"Notification error: {e}")
    
    return request

def create_cleaning_service_request(db: Session, room_id: int, room_number: str, guest_name: str = None, branch_id: Optional[int] = None):
    """
    Create a cleaning service request after checkout.
    This is automatically triggered when a room is checked out.
    """
    request = ServiceRequest(
        food_order_id=None,  # Cleaning requests don't have food orders
        room_id=room_id,
        employee_id=None,  # Will be assigned later
        request_type="cleaning",
        description=f"Room cleaning required after checkout - Room {room_number}" + (f" (Guest: {guest_name})" if guest_name else ""),
        status="pending",
        branch_id=branch_id
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    
    # Notify about new cleaning request
    try:
        notify_service_request_created(db, "cleaning", room_number, request.id, branch_id=branch_id)
    except Exception as e:
        print(f"Notification error: {e}")
    
    return request

def create_refill_service_request(db: Session, room_id: int, room_number: str, guest_name: str = None, checkout_id: int = None, branch_id: Optional[int] = None):
    """
    Create a refill service request after checkout for DAMAGED FIXED ASSETS ONLY.
    This service is specifically for replacing damaged permanent room fixtures/assets,
    NOT for consumables, rental items, or other inventory.
    """
    import json
    refill_items = []
    
    # Get refill requirements from checkout verification if checkout_id is provided
    if checkout_id:
        from app.models.checkout import CheckoutVerification, CheckoutRequest as CheckoutRequestModel
        from app.models.inventory import InventoryItem, AssetMapping, InventoryCategory
        from app.models.room import Room
        
        # Get the room to access its inventory location
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room or not room.inventory_location_id:
            return None  # No refill needed if room has no inventory location
        
        # Get the checkout request for this checkout to access inventory_data
        checkout_request = db.query(CheckoutRequestModel).filter(
            CheckoutRequestModel.checkout_id == checkout_id,
            CheckoutRequestModel.room_number == room_number
        ).first()
        
        if checkout_request and checkout_request.inventory_data:
            # Process inventory data to find ONLY damaged fixed assets
            for item in checkout_request.inventory_data:
                try:
                    item_id = item.get('item_id')
                    damage_qty = float(item.get('damage_qty', 0))
                    is_fixed_asset = item.get('is_fixed_asset', False)
                    
                    # CRITICAL FILTER: Only include items that are:
                    # 1. Fixed assets (is_fixed_asset = True)
                    # 2. Damaged (damage_qty > 0)
                    # 3. Assigned to this room (via AssetMapping)
                    if not is_fixed_asset or damage_qty <= 0:
                        continue
                    
                    # Verify this is a permanently assigned fixed asset
                    asset_mapping = db.query(AssetMapping).filter(
                        AssetMapping.location_id == room.inventory_location_id,
                        AssetMapping.item_id == item_id,
                        AssetMapping.is_active == True
                    ).first()
                    
                    if not asset_mapping:
                        # Not a permanently assigned asset, skip
                        continue
                    
                    # Get inventory item details
                    inv_item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
                    if inv_item:
                        # Verify it's truly a fixed asset from category
                        category = db.query(InventoryCategory).filter(
                            InventoryCategory.id == inv_item.category_id
                        ).first()
                        
                        is_asset_category = (
                            category and 
                            (category.is_asset_fixed or 
                             (category.classification and 'asset' in category.classification.lower()))
                        )
                        
                        if not is_asset_category and not inv_item.is_asset_fixed:
                            # Not truly a fixed asset, skip
                            continue
                        
                        # This is a damaged fixed asset that needs replacement
                        refill_items.append({
                            "item_id": item_id,
                            "item_name": inv_item.name,
                            "item_code": inv_item.item_code,
                            "quantity_to_refill": damage_qty,
                            "unit": inv_item.unit or "pcs",
                            "is_fixed_asset": True
                        })
                except (ValueError, KeyError, TypeError) as e:
                    print(f"[REFILL] Error processing item: {e}")
                    continue
    
    # Only create service request if there are damaged fixed assets to replace
    if not refill_items:
        print(f"[REFILL] No damaged fixed assets found for room {room_number}, skipping refill service request")
        return None
    
    # Build description with refill requirements
    description_parts = [f"Replace damaged fixed assets in Room {room_number}"]
    if guest_name:
        description_parts.append(f"Previous Guest: {guest_name}")
    
    description_parts.append("Damaged Assets to Replace:")
    for item in refill_items:
        description_parts.append(f"- {item['item_name']}: {item['quantity_to_refill']} {item['unit']}")
    
    request = ServiceRequest(
        food_order_id=None,
        room_id=room_id,
        employee_id=None,  # Will be assigned later
        request_type="refill",
        description=" | ".join(description_parts),
        refill_data=json.dumps(refill_items) if refill_items else None,
        status="pending",
        branch_id=branch_id
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    print(f"[REFILL] Created refill service request for {len(refill_items)} damaged fixed assets in room {room_number}")
    return request

def create_return_items_service_request(db: Session, room_id: int, room_number: str, guest_name: str = None, checkout_id: int = None, branch_id: Optional[int] = None):
    """
    Create a return items service request after checkout.
    This tells staff to collect unused items from the room and return them to warehouse.
    """
    import json
    return_items = []
    
    # Get items that need to be returned from checkout verification
    if checkout_id:
        from app.models.checkout import CheckoutVerification
        from app.models.inventory import InventoryItem, LocationStock
        
        # Get the checkout verification for this room
        verification = db.query(CheckoutVerification).filter(
            CheckoutVerification.checkout_id == checkout_id,
            CheckoutVerification.room_number == room_number
        ).first()
        
        if verification and verification.consumables_audit_data:
            # Extract consumables data and find unused items
            consumables_data = verification.consumables_audit_data
            
            for item_id_str, item_data in consumables_data.items():
                try:
                    item_id = int(item_id_str)
                    issued_qty = item_data.get("issued", 0)
                    actual_consumed = item_data.get("actual", 0)
                    is_rentable = item_data.get("is_rentable", False)
                    missing_qty = item_data.get("missing", 0)
                    
                    if is_rentable:
                        # For rentables, we must return everything that wasn't lost/missing
                        # Even if it was "used" (rented), the physical item must be returned to storage
                        returned_qty = issued_qty - missing_qty
                    else:
                        # For consumables, we return what wasn't used OR missing
                        returned_qty = issued_qty - actual_consumed
                    
                    if returned_qty > 0:
                        # Get inventory item details
                        inv_item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
                        if inv_item:
                            return_items.append({
                                "item_id": item_id,
                                "item_name": inv_item.name,
                                "item_code": inv_item.item_code,
                                "quantity_to_return": returned_qty,
                                "unit": inv_item.unit or "pcs",
                                "is_rentable": is_rentable
                            })
                except (ValueError, KeyError):
                    continue
    
    # Only create service request if there are items to return
    if not return_items:
        return None
    
    # Build description with return requirements
    description_parts = [f"Collect and return unused items to warehouse - Room {room_number}"]
    if guest_name:
        description_parts.append(f"Previous Guest: {guest_name}")
    
    description_parts.append("Items to Return:")
    for item in return_items:
        description_parts.append(f"- {item['item_name']}: {item['quantity_to_return']} {item['unit']}")
    
    request = ServiceRequest(
        food_order_id=None,
        room_id=room_id,
        employee_id=None,  # Will be assigned later
        request_type="return_items",
        description=" | ".join(description_parts),
        refill_data=json.dumps(return_items),  # Store return items as JSON
        status="pending",
        branch_id=branch_id
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request

def get_service_requests(db: Session, skip: int = 0, limit: int = 100, status: Optional[str] = None, room_id: Optional[int] = None, employee_id: Optional[int] = None, branch_id: int = None):
    from sqlalchemy.orm import selectinload
    query = db.query(ServiceRequest).options(
        joinedload(ServiceRequest.room),
        joinedload(ServiceRequest.employee),
        joinedload(ServiceRequest.food_order).options(
            selectinload(FoodOrder.items).joinedload(FoodOrderItem.food_item)
        )
    )
    
    if branch_id:
        query = query.filter(ServiceRequest.branch_id == branch_id)

    
    if status:
        query = query.filter(ServiceRequest.status == status)
    
    if room_id:
        query = query.filter(ServiceRequest.room_id == room_id)

    if employee_id is not None:
        from sqlalchemy import or_
        query = query.filter(or_(ServiceRequest.employee_id == employee_id, ServiceRequest.employee_id == None))
    
    requests = query.offset(skip).limit(limit).all()
    
    # Enrich with additional data
    for req in requests:
        if req.food_order:
            req.food_order_amount = req.food_order.amount
            req.food_order_status = req.food_order.status
            req.food_order_billing_status = req.food_order.billing_status
            req.food_items = req.food_order.items
        if req.room:
            req.room_number = req.room.number
        # Always set employee_name, even if None
        req.employee_name = req.employee.name if req.employee else None
    
    return requests

def get_service_request(db: Session, request_id: int):
    request = db.query(ServiceRequest).options(
        joinedload(ServiceRequest.food_order),
        joinedload(ServiceRequest.room),
        joinedload(ServiceRequest.employee)
    ).options(
        joinedload(ServiceRequest.food_order).joinedload(FoodOrder.items).joinedload(FoodOrderItem.food_item)
    ).filter(ServiceRequest.id == request_id).first()
    
    if request:
        if request.food_order:
            request.food_order_amount = request.food_order.amount
            request.food_order_status = request.food_order.status
            request.food_order_billing_status = request.food_order.billing_status
            request.food_items = request.food_order.items
        if request.room:
            request.room_number = request.room.number
        # Always set employee_name, even if None
        request.employee_name = request.employee.name if request.employee else None
    
    return request

def update_service_request(db: Session, request_id: int, update_data: ServiceRequestUpdate, branch_id: int):
    query = db.query(ServiceRequest).filter(ServiceRequest.id == request_id)
    if branch_id:  # Only filter by branch if a specific branch is specified (not enterprise/all view)
        query = query.filter(ServiceRequest.branch_id == branch_id)
    request = query.first()
    if not request:
        return None
    
    old_status = request.status
    
    # Track if status is changing to completed
    is_completing = False
    if update_data.status is not None and update_data.status == "completed" and request.status != "completed":
        is_completing = True
    
    if update_data.status is not None:
        request.status = update_data.status
        
    if update_data.billing_status is not None:
        request.billing_status = update_data.billing_status

    if update_data.status == "in_progress" and not request.started_at:
        request.started_at = datetime.now(timezone.utc)
        print(f"[DEBUG] Set started_at for ServiceRequest {request_id}: {request.started_at}")
    elif update_data.status == "completed":
        request.completed_at = datetime.now(timezone.utc)
            
        # Resolve linked user for transaction logging (avoid FK violation if employee_id != user_id)
        acting_user_id = None
        acting_emp_id = update_data.employee_id or request.employee_id
        if acting_emp_id:
            acting_emp = db.query(Employee).filter(Employee.id == acting_emp_id, Employee.branch_id == branch_id).first()
            if acting_emp:
                acting_user_id = acting_emp.user_id

        # If this is a delivery request with a food order, update the food order status
        if request.food_order_id:
            food_order = db.query(FoodOrder).filter(FoodOrder.id == request.food_order_id, FoodOrder.branch_id == branch_id).first()
            if food_order:
                if is_completing:
                    # Mark food order as completed
                    food_order.status = "completed"
                    
                    # Use billing_status from update_data if provided, otherwise default to unpaid
                    if update_data.billing_status:
                        food_order.billing_status = update_data.billing_status
                    elif food_order.billing_status != "paid":
                        food_order.billing_status = "unpaid"
                    
                    print(f"[INFO] Food order {food_order.id} marked as completed (billing: {food_order.billing_status}) due to delivery service completion")
                elif update_data.status == "cancelled":
                    # Mark food order as cancelled
                    food_order.status = "cancelled"
                    print(f"[INFO] Food order {food_order.id} marked as cancelled due to delivery service cancellation")

        # NEW: Handle Inventory Movement for 'return_items' completion
        if request.request_type == "return_items" and is_completing:
            try:
                import json
                from app.models.inventory import LocationStock, InventoryTransaction, Location, InventoryItem, AssetMapping
                
                # 1. Determine target location (default to Warehouse if not provided)
                target_loc_id = update_data.return_location_id
                if not target_loc_id:
                     wh_query = db.query(Location).filter(Location.location_type == "WAREHOUSE")
                     if branch_id:
                         wh_query = wh_query.filter(Location.branch_id == branch_id)
                     wh = wh_query.first()
                     target_loc_id = wh.id if wh else None
                
                if target_loc_id and request.refill_data and request.room_id:
                    room = db.query(Room).filter(Room.id == request.room_id, Room.branch_id == branch_id).first()
                    return_items = json.loads(request.refill_data)
                    
                    if room and room.inventory_location_id:
                        for item_data in return_items:
                            item_id = item_data.get("item_id")
                            qty_to_move = float(item_data.get("quantity_to_return", 0))
                            is_rentable = item_data.get("is_rentable", False)
                            
                            if item_id and qty_to_move > 0:
                                # Find room stock
                                room_stock = db.query(LocationStock).filter(
                                    LocationStock.location_id == room.inventory_location_id,
                                    LocationStock.item_id == item_id
                                ).first()
                                
                                # Only move if room has enough stock (capped to avoid inconsistencies)
                                actual_move = min(qty_to_move, room_stock.quantity if room_stock else 0)
                                if actual_move > 0:
                                    # Deduct from Room
                                    room_stock.quantity -= actual_move
                                    
                                    # Add to Target Location (e.g. Warehouse)
                                    target_stock = db.query(LocationStock).filter(
                                        LocationStock.location_id == target_loc_id,
                                        LocationStock.item_id == item_id
                                    ).first()
                                    
                                    if target_stock:
                                        target_stock.quantity += actual_move
                                    else:
                                        db.add(LocationStock(
                                            location_id=target_loc_id,
                                            item_id=item_id,
                                            quantity=actual_move
                                        ))
                                    
                                    # CRITICAL FIX: Deactivate AssetMapping for fixed assets/rentables
                                    # This ensures they don't show in room inventory anymore
                                    if is_rentable:
                                        # Deactivate asset mappings for this item in this room
                                        asset_mappings = db.query(AssetMapping).filter(
                                            AssetMapping.location_id == room.inventory_location_id,
                                            AssetMapping.item_id == item_id,
                                            AssetMapping.is_active == True
                                        ).all()
                                        
                                        deactivated_count = 0
                                        for mapping in asset_mappings:
                                            if deactivated_count < actual_move:
                                                mapping.is_active = False
                                                deactivated_count += 1
                                                print(f"[INVENTORY] Deactivated AssetMapping for {item_data.get('item_name')} in Room {room.number}")
                                    
                                    # Log Transaction
                                    db.add(InventoryTransaction(
                                        item_id=item_id,
                                        transaction_type="transfer",
                                        quantity=actual_move,
                                        reference_number=f"RET-SR-{request.id}",
                                        notes=f"Return from Room {room.number} via Service Request",
                                        created_by=acting_user_id
                                    ))
                                    print(f"[INVENTORY] Moved {actual_move} of item {item_id} from Room {room.number} to Loc {target_loc_id}")
            except Exception as e:
                print(f"[ERROR] Failed to process return items inventory movement: {e}")

        # NEW: Handle Inventory Movement for 'replenishment' or 'refill' completion
        if request.request_type in ["replenishment", "refill"] and is_completing:
            try:
                import json
                from app.models.inventory import LocationStock, InventoryTransaction, AssetMapping, InventoryItem, AssetRegistry, Location

                # 1. Determine Source Location (Pickup Location)
                source_loc_id = request.pickup_location_id
                if not source_loc_id:
                    # Default to Warehouse if not set
                    wh_query = db.query(Location).filter(Location.location_type == "WAREHOUSE")
                    if branch_id:
                        wh_query = wh_query.filter(Location.branch_id == branch_id)
                    wh = wh_query.first()
                    source_loc_id = wh.id if wh else None
                    print(f"[REPLENISHMENT] Pickup location not set for request {request.id}. Defaulting to Warehouse (Loc {source_loc_id}).")
                
                if not source_loc_id:
                    print(f"[REPLENISHMENT] No pickup location available, skipping automated stock movement.")
                else:
                    if request.refill_data and request.room_id:
                        room = db.query(Room).filter(Room.id == request.room_id, Room.branch_id == branch_id).first()
                        replenish_items = json.loads(request.refill_data)
                        
                        if room and room.inventory_location_id:
                            for item_data in replenish_items:
                                item_id = item_data.get("item_id")
                                # Support both 'quantity' and 'quantity_to_refill' keys
                                qty_to_move = float(item_data.get("quantity") or item_data.get("quantity_to_refill") or 1)
                                is_fixed_asset = item_data.get("is_fixed_asset", False) or item_data.get("is_asset", False)
                                
                                if item_id:
                                    # Deduct from Pickup Location
                                    pickup_stock = db.query(LocationStock).filter(
                                        LocationStock.location_id == source_loc_id,
                                        LocationStock.item_id == item_id
                                    ).first()

                                    if pickup_stock:
                                        if pickup_stock.quantity >= qty_to_move:
                                            pickup_stock.quantity -= qty_to_move
                                        else:
                                            print(f"[REPLENISHMENT] Warning: Insufficient stock at pickup loc {source_loc_id} for item {item_id}. Proceeding correctly anyway.")
                                            pickup_stock.quantity = 0 # Consume whatever is there or go negative? Better to just set 0 if low.
                                    else:
                                         print(f"[REPLENISHMENT] Warning: No stock record at pickup loc {source_loc_id} for item {item_id}.")
                                    
                                    # Add to Room Location
                                    room_stock = db.query(LocationStock).filter(
                                        LocationStock.location_id == room.inventory_location_id,
                                        LocationStock.item_id == item_id
                                    ).first()
                                    
                                    if room_stock:
                                        room_stock.quantity += qty_to_move
                                    else:
                                        db.add(LocationStock(
                                            location_id=room.inventory_location_id,
                                            item_id=item_id,
                                            quantity=qty_to_move,
                                            last_updated=datetime.now(timezone.utc)
                                        ))
                                    
                                    # Log Transaction
                                    db.add(InventoryTransaction(
                                        item_id=item_id,
                                        transaction_type="transfer",
                                        quantity=qty_to_move,
                                        reference_number=f"RPL-SR-{request.id}",
                                        notes=f"Replenishment for Room {room.number} from Loc {source_loc_id}",
                                        created_by=acting_user_id
                                    ))
                                    
                                    # FIXED ASSETS: Re-activate mapping or update registry?
                                    # If it's a fixed asset, we might want to update AssetRegistry location if we are tracking specific serials.
                                    # But often Replenishment is just "bring a generic bed sheet".
                                    # If we have deactivated mapping previously, we should re-activate one?
                                    if is_fixed_asset:
                                        # Find an inactive mapping and activate it to restore "standard" state
                                        inactive_mapping = db.query(AssetMapping).filter(
                                            AssetMapping.location_id == room.inventory_location_id,
                                            AssetMapping.item_id == item_id,
                                            AssetMapping.is_active == False
                                        ).first()
                                        
                                        if inactive_mapping:
                                            inactive_mapping.is_active = True
                                            print(f"[REPLENISHMENT] Re-activated AssetMapping for {item_id} in Room {room.number}")
                                        
                                    print(f"[INVENTORY] Replenished {qty_to_move} of item {item_id} to Room {room.number} from Loc {source_loc_id}")

            except Exception as e:
                print(f"[ERROR] Failed to process replenishment items inventory movement: {e}")

        # Sync with AssignedService: Heuristic to auto-complete duplicate manual assignments
        if is_completing:
            try:
                from app.models.service import AssignedService, Service
                from app.curd.service import update_assigned_service_status
                from app.schemas.service import AssignedServiceUpdate

                target_employee_id = update_data.employee_id or request.employee_id
                
                if target_employee_id and request.room_id:
                    # Use nested transaction to isolate failures
                    try:
                        with db.begin_nested():
                            # Find pending assigned services for this room/employee
                            query = db.query(AssignedService).join(Service).filter(
                                AssignedService.room_id == request.room_id,
                                AssignedService.employee_id == target_employee_id,
                                AssignedService.status.notin_(['completed', 'cancelled'])
                            )
                            
                            # Apply name filter based on request type to avoid false positives
                            if request.request_type == 'delivery':
                                query = query.filter(
                                    Service.name.ilike('%food%') | 
                                    Service.name.ilike('%delivery%') | 
                                    Service.name.ilike('%milk%') | 
                                    Service.name.ilike('%water%') | 
                                    Service.name.ilike('%tea%') | 
                                    Service.name.ilike('%coffee%') | 
                                    Service.name.ilike('%breakfast%') | 
                                    Service.name.ilike('%lunch%') | 
                                    Service.name.ilike('%dinner%') | 
                                    Service.name.ilike('%beverage%')
                                )
                            elif request.request_type == 'cleaning':
                                query = query.filter(Service.name.ilike('%clean%') | Service.name.ilike('%housekeep%') | Service.name.ilike('%room%'))
                            elif request.request_type == 'refill':
                                query = query.filter(Service.name.ilike('%refill%') | Service.name.ilike('%return%'))
                            
                            # Only auto-complete services assigned within the last 48 hours to be safe
                            matching_services = query.all()
                            
                            for svc in matching_services:
                                # Verify timestamp safely
                                assigned_time = svc.assigned_at or datetime.now(timezone.utc)
                                time_diff = datetime.now(timezone.utc) - assigned_time
                                if time_diff.total_seconds() < 172800: # 48 hours
                                    print(f"[INFO] Auto-completing linked AssignedService {svc.id} ({svc.service.name}) matching ServiceRequest {request.id}")
                                    update_assigned_service_status(db, svc.id, AssignedServiceUpdate(status='completed'), commit=False)
                    except Exception as nested_error:
                        print(f"[WARNING] Nested transaction failed during AssignedService sync: {nested_error}")
                        import traceback
                        print(traceback.format_exc())
                        # Don't rollback - continue with main update even if sync fails
            except Exception as sync_error:
                print(f"[WARNING] Failed to sync AssignedService status: {sync_error}")
                import traceback
                print(traceback.format_exc())
                # Don't rollback - continue with main update even if sync fails

    if update_data.employee_id is not None:
        request.employee_id = update_data.employee_id
    if update_data.pickup_location_id is not None:
        request.pickup_location_id = update_data.pickup_location_id
    if update_data.description is not None:
        request.description = update_data.description
    
    db.commit()
    db.refresh(request)
    
    
    # Notify about status change
    try:
        room = db.query(Room).filter(Room.id == request.room_id, Room.branch_id == branch_id).first()
        room_number = room.number if room else "Unknown"
        
        recipient_id = None
        if request.employee_id:
            emp = db.query(Employee).filter(Employee.id == request.employee_id, Employee.branch_id == branch_id).first()
            if emp:
                recipient_id = emp.user_id
        
        notify_service_request_status_changed(db, request.request_type, room_number, request.status, request.id, branch_id=branch_id, recipient_id=recipient_id)
    except Exception as e:
        print(f"Notification error: {e}")
    
    return request

def delete_service_request(db: Session, request_id: int):
    request = db.query(ServiceRequest).filter(ServiceRequest.id == request_id).first()
    if request:
        db.delete(request)
        db.commit()
    return request

