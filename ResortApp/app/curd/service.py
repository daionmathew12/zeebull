from sqlalchemy.orm import Session, joinedload, noload
from sqlalchemy import select, func
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError, IntegrityError
from typing import List, Optional
from datetime import timezone, date, datetime
from app.models.service import Service, AssignedService, ServiceImage, service_inventory_item
from app.models.inventory import (
    InventoryItem, 
    InventoryTransaction, 
    Location, 
    LocationStock, 
    LaundryLog, 
    WasteLog
)
from app.models.employee_inventory import EmployeeInventoryAssignment
from app.curd import inventory as crud_inventory
from app.models.booking import Booking, BookingRoom
from app.models.Package import PackageBooking, PackageBookingRoom
from app.models.employee import Employee
from app.models.room import Room
from app.curd.notification import notify_service_assigned, notify_service_status_changed
from app.schemas.service import (
    ServiceInventoryItemBase, 
    AssignedServiceCreate, 
    AssignedServiceUpdate
)

def create_service(
    db: Session,
    name: str,
    description: str,
    charges: float,
    image_urls: List[str] = None,
    inventory_items: Optional[List[ServiceInventoryItemBase]] = None,
    is_visible_to_guest: bool = False,
    average_completion_time: Optional[str] = None,
    branch_id: int = 1
):

    """
    Create a new service with optional images and inventory items.
    Gracefully handles missing permissions on the service_inventory_items table
    by creating the service and skipping the association instead of failing.
    """
    import traceback

    try:
        # 1. Create the service record
        db_service = Service(
            name=name,
            description=description,
            charges=charges,
            is_visible_to_guest=is_visible_to_guest,
            average_completion_time=average_completion_time,
            branch_id=branch_id
        )

        db.add(db_service)
        db.commit()
        db.refresh(db_service)
    except Exception as create_error:
        db.rollback()
        error_msg = f"Failed to create service: {str(create_error)}"
        print(f"[ERROR create_service CRUD] {error_msg}")
        print(traceback.format_exc())
        raise ValueError(error_msg) from create_error

    # 2. Attach images (if any)
    if image_urls:
        try:
            for url in image_urls:
                if url:
                    db.add(ServiceImage(service_id=db_service.id, image_url=url))
            db.commit()
            db.refresh(db_service)
        except Exception as img_error:
            db.rollback()
            error_msg = f"Failed to add service images: {str(img_error)}"
            print(f"[ERROR create_service CRUD] {error_msg}")
            print(traceback.format_exc())
            raise ValueError(error_msg) from img_error

    # 3. Link inventory items (best-effort; skip if insufficient privileges)
    if inventory_items:
        inventory_insert_failed = False
        permission_error = False
        inserted_count = 0
        try:
            print(f"[DEBUG create_service] Attempting to link {len(inventory_items)} inventory items to service {db_service.id}")
            for item_data in inventory_items:
                print(f"[DEBUG create_service] Processing inventory item: id={item_data.inventory_item_id}, quantity={item_data.quantity}")
                inventory_item = (
                    db.query(InventoryItem)
                    .filter(InventoryItem.id == item_data.inventory_item_id)
                    .first()
                )
                if not inventory_item:
                    print(
                        f"[WARNING] Inventory item {item_data.inventory_item_id} not found, skipping"
                    )
                    continue

                stmt = service_inventory_item.insert().values(
                    service_id=db_service.id,
                    inventory_item_id=item_data.inventory_item_id,
                    quantity=item_data.quantity,
                    created_at=datetime.now(timezone.utc)  # Explicitly set created_at
                )
                result = db.execute(stmt)
                inserted_count += 1
                print(f"[DEBUG create_service] Successfully inserted inventory link: service_id={db_service.id}, item_id={item_data.inventory_item_id}, quantity={item_data.quantity}")

            db.commit()
            print(f"[DEBUG create_service] Successfully committed {inserted_count} inventory item links for service {db_service.id}")
            
            # Verify the data was actually saved
            try:
                verify_stmt = select(
                    service_inventory_item.c.inventory_item_id,
                    service_inventory_item.c.quantity
                ).where(service_inventory_item.c.service_id == db_service.id)
                verify_rows = db.execute(verify_stmt).fetchall()
                print(f"[DEBUG create_service] Verification: Found {len(verify_rows)} inventory item links in database for service {db_service.id}")
                for row in verify_rows:
                    item_id = row[0] if isinstance(row, tuple) else getattr(row, 'inventory_item_id', row[0])
                    qty = row[1] if isinstance(row, tuple) else getattr(row, 'quantity', row[1])
                    print(f"[DEBUG create_service]   - Item ID: {item_id}, Quantity: {qty}")
            except Exception as verify_error:
                print(f"[WARNING] Could not verify saved inventory items: {verify_error}")
        except ProgrammingError as perm_error:
            permission_error = True
            inventory_insert_failed = True
            db.rollback()
            print(
                f"[ERROR] Insufficient privilege linking inventory items for service {db_service.id}: {perm_error}"
            )
            print(traceback.format_exc())
        except SQLAlchemyError as link_error:
            inventory_insert_failed = True
            db.rollback()
            print(
                f"[ERROR] Failed to link inventory items for service {db_service.id}: {link_error}"
            )
            print(traceback.format_exc())

        if inventory_insert_failed:
            msg = (
                "Some inventory items could not be linked because the database user "
                "lacks permission to access service_inventory_items."
                if permission_error
                else "Some inventory items failed to link due to a database error."
            )
            print(f"[WARNING] {msg} Service ID: {db_service.id}")
        else:
            print(f"[SUCCESS] All {inserted_count} inventory items successfully linked to service {db_service.id}")

    # 4. Return the service with related images
    try:
        service = (
            db.query(Service)
            .options(joinedload(Service.images))
            .filter(Service.id == db_service.id)
            .first()
        )
        return service or db_service
    except Exception as load_error:
        print(
            f"[WARNING] Failed to load service relationships for service {db_service.id}: {load_error}"
        )
        print(traceback.format_exc())
        return db_service

def update_service(
    db: Session,
    service_id: int,
    name: str,
    description: str,
    charges: float,
    new_image_urls: Optional[List[str]] = None,
    images_to_remove: Optional[List[int]] = None,
    inventory_items: Optional[List[ServiceInventoryItemBase]] = None,
    is_visible_to_guest: bool = False,
    average_completion_time: Optional[str] = None
):
    """
    Update an existing service. Supports adding new images, removing selected images,
    and updating inventory assignments (best-effort if DB permissions allow).
    Returns tuple of (service, removed_image_paths).
    """
    import traceback

    service = db.query(Service).options(joinedload(Service.images)).filter(Service.id == service_id).first()
    if not service:
        raise ValueError(f"Service with ID {service_id} not found")

    removed_image_paths: List[str] = []

    try:
        service.name = name
        service.description = description
        service.charges = charges
        service.is_visible_to_guest = is_visible_to_guest
        if average_completion_time is not None:
            service.average_completion_time = average_completion_time

        # Remove selected images
        if images_to_remove:
            images = (
                db.query(ServiceImage)
                .filter(ServiceImage.service_id == service_id, ServiceImage.id.in_(images_to_remove))
                .all()
            )
            for img in images:
                removed_image_paths.append(img.image_url)
                db.delete(img)

        # Add new images
        if new_image_urls:
            for url in new_image_urls:
                if url:
                    db.add(ServiceImage(service_id=service_id, image_url=url))

        db.commit()
        db.refresh(service)
    except Exception as update_error:
        db.rollback()
        error_msg = f"Failed to update service {service_id}: {str(update_error)}"
        print(f"[ERROR update_service CRUD] {error_msg}")
        print(traceback.format_exc())
        raise ValueError(error_msg) from update_error

    # Handle inventory updates (best-effort)
    if inventory_items is not None:
        permission_error = False
        try:
            print(f"[DEBUG update_service] Updating inventory items for service {service_id}")
            # First, check what's currently in the database
            try:
                before_stmt = select(
                    service_inventory_item.c.inventory_item_id,
                    service_inventory_item.c.quantity
                ).where(service_inventory_item.c.service_id == service_id)
                before_rows = db.execute(before_stmt).fetchall()
                print(f"[DEBUG update_service] Current inventory items in DB: {len(before_rows)}")
            except Exception as check_error:
                print(f"[WARNING] Could not check existing inventory items: {check_error}")
            
            delete_stmt = service_inventory_item.delete().where(service_inventory_item.c.service_id == service_id)
            delete_result = db.execute(delete_stmt)
            deleted_count = delete_result.rowcount if hasattr(delete_result, 'rowcount') else 0
            db.commit()
            print(f"[DEBUG update_service] Deleted {deleted_count} existing inventory item links")

            if inventory_items:
                inserted_count = 0
                for item_data in inventory_items:
                    print(f"[DEBUG update_service] Processing inventory item: id={item_data.inventory_item_id}, quantity={item_data.quantity}")
                    inventory_item = (
                        db.query(InventoryItem)
                        .filter(InventoryItem.id == item_data.inventory_item_id)
                        .first()
                    )
                    if not inventory_item:
                        print(f"[WARNING] Inventory item {item_data.inventory_item_id} not found, skipping")
                        continue

                    insert_stmt = service_inventory_item.insert().values(
                        service_id=service_id,
                        inventory_item_id=item_data.inventory_item_id,
                        quantity=item_data.quantity,
                        created_at=datetime.now(timezone.utc)  # Explicitly set created_at
                    )
                    db.execute(insert_stmt)
                    inserted_count += 1
                    print(f"[DEBUG update_service] Successfully inserted inventory link: service_id={service_id}, item_id={item_data.inventory_item_id}, quantity={item_data.quantity}")
                db.commit()
                print(f"[DEBUG update_service] Successfully committed {inserted_count} inventory item links for service {service_id}")
                
                # Verify the data was actually saved
                try:
                    verify_stmt = select(
                        service_inventory_item.c.inventory_item_id,
                        service_inventory_item.c.quantity
                    ).where(service_inventory_item.c.service_id == service_id)
                    verify_rows = db.execute(verify_stmt).fetchall()
                    print(f"[DEBUG update_service] Verification: Found {len(verify_rows)} inventory item links in database for service {service_id}")
                    for row in verify_rows:
                        item_id = row[0] if isinstance(row, tuple) else getattr(row, 'inventory_item_id', row[0])
                        qty = row[1] if isinstance(row, tuple) else getattr(row, 'quantity', row[1])
                        print(f"[DEBUG update_service]   - Item ID: {item_id}, Quantity: {qty}")
                except Exception as verify_error:
                    print(f"[WARNING] Could not verify saved inventory items: {verify_error}")
            else:
                print(f"[DEBUG update_service] No inventory items to insert (empty list)")
        except ProgrammingError as perm_error:
            permission_error = True
            db.rollback()
            print(
                f"[WARNING] Insufficient privilege updating inventory items for service {service_id}: {perm_error}"
            )
            print(traceback.format_exc())
        except SQLAlchemyError as link_error:
            db.rollback()
            print(f"[WARNING] Failed to update inventory items for service {service_id}: {link_error}")
            print(traceback.format_exc())

        if permission_error:
            print(
                f"[WARNING] Inventory items might be outdated for service {service_id} due to missing DB permissions"
            )

        try:
            db.refresh(service)
        except Exception:
            pass

    return service, removed_image_paths

def get_services(db: Session, skip: int = 0, limit: int = 100, branch_id: int = None):
    query = db.query(Service).options(
        joinedload(Service.images)
    )
    if branch_id:
        query = query.filter(Service.branch_id == branch_id)
    return query.offset(skip).limit(limit).all()


def delete_service(db: Session, service_id: int):
    import traceback

    service = (
        db.query(Service)
        .options(
            joinedload(Service.images),
            noload(Service.inventory_items)
        )
        .filter(Service.id == service_id)
        .first()
    )
    if not service:
        raise ValueError(f"Service with ID {service_id} not found")

    image_paths = [img.image_url for img in (service.images or [])]

    try:
        db.delete(service)
        db.commit()
        return image_paths
    except IntegrityError as fk_error:
        db.rollback()
        message = (
            "Cannot delete service because it is still referenced by assigned services "
            "or other records. Please unassign or remove related records first."
        )
        print(f"[WARNING delete_service CRUD] {message} Service ID: {service_id}")
        print(fk_error)
        raise ValueError(message) from fk_error
    except ProgrammingError as perm_error:
        db.rollback()
        message = (
            "Cannot delete service because the database user lacks permission "
            "to modify the service inventory mapping table. Please contact your administrator."
        )
        print(f"[WARNING delete_service CRUD] Permission issue deleting service {service_id}: {perm_error}")
        raise ValueError(message) from perm_error
    except Exception as delete_error:
        db.rollback()
        print(f"[ERROR delete_service CRUD] Failed to delete service {service_id}: {delete_error}")
        print(traceback.format_exc())
        raise RuntimeError(f"Failed to delete service: {delete_error}") from delete_error

def create_assigned_service(db: Session, assigned: AssignedServiceCreate, branch_id: int = 1):

    try:
        # Convert Pydantic model to dict (handle both .model_dump() and .model_dump())
        if hasattr(assigned, 'model_dump'):
            assigned_dict = assigned.model_dump()
        else:
            assigned_dict = assigned.model_dump()
        assigned_dict['branch_id'] = branch_id if branch_id is not None else 1

        
        print(f"[DEBUG] Creating assigned service with data: {assigned_dict}")
        
        # Verify that required IDs exist
        service = db.query(Service).filter(Service.id == assigned_dict['service_id']).first()
        if not service:
            raise ValueError(f"Service with ID {assigned_dict['service_id']} not found")
        
        employee = db.query(Employee).filter(Employee.id == assigned_dict['employee_id']).first()
        if not employee:
            raise ValueError(f"Employee with ID {assigned_dict['employee_id']} not found")
        
        room = db.query(Room).filter(Room.id == assigned_dict['room_id']).first()
        if not room:
            raise ValueError(f"Room with ID {assigned_dict['room_id']} not found")
        
        print(f"[DEBUG] All references valid: Service={service.name}, Employee={employee.name}, Room={room.number}")
        
        # Load service inventory items if service has any
        service_inventory_items = []
        # Query association table for quantities (best-effort)
        associations = []
        try:
            stmt = select(service_inventory_item).where(service_inventory_item.c.service_id == service.id)
            associations = db.execute(stmt).fetchall()
            print(f"[DEBUG] Found {len(associations)} inventory item associations for service {service.id}")
        except Exception as assoc_err:
            db.rollback()
            print(f"[WARNING] Unable to read service inventory items for service {service.id}: {str(assoc_err)}")
            import traceback
            print(traceback.format_exc())
            associations = []
        
        for assoc in associations:
            # Get inventory item directly from database
            inv_item = db.query(InventoryItem).filter(InventoryItem.id == assoc.inventory_item_id).first()
            if inv_item:
                service_inventory_items.append({
                    'item_id': inv_item.id,
                    'item_name': inv_item.name,
                    'quantity': assoc.quantity,
                    'unit': inv_item.unit
                })
                print(f"[DEBUG] Added inventory item: {inv_item.name} (ID: {inv_item.id}), Quantity: {assoc.quantity}")
            else:
                print(f"[WARNING] Inventory item ID {assoc.inventory_item_id} not found in database")
        
        print(f"[DEBUG] Service has {len(service_inventory_items)} inventory items from template")
        
        # Add extra inventory items if provided
        extra_items = assigned_dict.get('extra_inventory_items', [])
        if extra_items:
            print(f"[DEBUG] Processing {len(extra_items)} extra inventory items")
            for extra_item in extra_items:
                inv_item = db.query(InventoryItem).filter(InventoryItem.id == extra_item['inventory_item_id']).first()
                if inv_item:
                    service_inventory_items.append({
                        'item_id': inv_item.id,
                        'item_name': inv_item.name,
                        'quantity': extra_item['quantity'],
                        'unit': inv_item.unit
                    })
                    print(f"[DEBUG] Added EXTRA inventory item: {inv_item.name} (ID: {inv_item.id}), Quantity: {extra_item['quantity']}")
                else:
                    print(f"[WARNING] Extra inventory item ID {extra_item['inventory_item_id']} not found in database")
        
        print(f"[DEBUG] Total inventory items to assign (template + extra): {len(service_inventory_items)}")
        
        # Try to link to a booking if not provided
        booking_id = assigned_dict.get('booking_id')
        package_booking_id = assigned_dict.get('package_booking_id')
        
        if not booking_id and not package_booking_id:
            from app.curd.foodorder import get_booking_for_room
            b_id, is_pkg = get_booking_for_room(assigned_dict['room_id'], db, branch_id=branch_id)
            if b_id:
                if is_pkg:
                    package_booking_id = b_id
                else:
                    booking_id = b_id

        # Create AssignedService instance (status will use default from model)
        try:
            db_assigned = AssignedService(
                service_id=assigned_dict['service_id'],
                employee_id=assigned_dict['employee_id'],
                room_id=assigned_dict['room_id'],
                booking_id=booking_id,
                package_booking_id=package_booking_id,
                override_charges=assigned_dict.get('override_charges'),
                billing_status=assigned_dict.get('billing_status', 'unbilled'),
                branch_id=assigned_dict.get('branch_id', 1)
            )

            print(f"[DEBUG] AssignedService object created, status={db_assigned.status}, billing_status={db_assigned.billing_status}")
            db.add(db_assigned)
            db.flush()  # Flush to get the ID without committing
            print(f"[DEBUG] AssignedService flushed, ID={db_assigned.id}")
            
            # Deduct inventory items if service requires them
            if service_inventory_items:
                # Build lookup for source selections
                source_map = {}
                selections = assigned_dict.get('inventory_source_selections', [])
                if selections:
                    for sel in selections:
                        # sel is likely a dict
                        iid = sel['item_id']
                        lid = sel['location_id']
                        source_map[iid] = lid
                
                print(f"[DEBUG] Inventory Source Map: {source_map}")

                # Default fallback location (Central Warehouse)
                default_location = db.query(Location).filter(
                    (func.upper(Location.location_type) == "WAREHOUSE") | 
                    (func.upper(Location.location_type) == "CENTRAL_WAREHOUSE") |
                    (Location.is_inventory_point == True)
                ).first()
                
                if not default_location:
                    # Fallback to any warehouse
                    default_location = db.query(Location).filter(
                        func.upper(Location.location_type).in_(["WAREHOUSE", "CENTRAL_WAREHOUSE", "BRANCH_STORE"])
                    ).first()
                
                # Check for EmployeeInventoryAssignment model
                try:
                    print("[DEBUG] Attempting to import EmployeeInventoryAssignment...")
                    from app.models.employee_inventory import EmployeeInventoryAssignment
                    has_emp_inv_model = True
                    print("[DEBUG] EmployeeInventoryAssignment imported successfully")
                except ImportError as e:
                    print(f"[WARNING] EmployeeInventoryAssignment model not found/import failed: {e}")
                    EmployeeInventoryAssignment = None
                    has_emp_inv_model = False
                except Exception as e:
                    print(f"[ERROR] Unexpected error importing EmployeeInventoryAssignment: {e}")
                    has_emp_inv_model = False

                for inv_data in service_inventory_items:
                    item_id = inv_data['item_id']
                    quantity = inv_data['quantity']
                    
                    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
                    if not item:
                        print(f"[WARNING] Inventory item {item_id} not found, skipping")
                        continue
                    
                    # Determine Source Location
                    source_loc_id = source_map.get(item_id)
                    source_location = None
                    
                    if source_loc_id:
                        source_location = db.query(Location).filter(Location.id == source_loc_id).first()
                    
                    if not source_location and default_location:
                        source_location = default_location
                        print(f"[DEBUG] Using default location {source_location.name} for item {item.name}")
                    
                    if source_location:
                        # 1. Deduct from LocationStock
                        loc_stock = db.query(LocationStock).filter(
                            LocationStock.location_id == source_location.id,
                            LocationStock.item_id == item_id
                        ).first()
                        
                        if loc_stock:
                            if loc_stock.quantity < quantity:
                                print(f"[WARNING] Insufficient stock at {source_location.name} for {item.name}. Available: {loc_stock.quantity}, Required: {quantity}. Proceeding anyway (negative stock).")
                            loc_stock.quantity -= quantity
                            loc_stock.last_updated = datetime.now(timezone.utc)
                        else:
                            print(f"[WARNING] No stock record at {source_location.name} for {item.name}. Creating negative entry.")
                            new_stock = LocationStock(
                                location_id=source_location.id,
                                item_id=item_id,
                                quantity=-quantity,
                                last_updated=datetime.now(timezone.utc)
                            )
                            db.add(new_stock)
                    else:
                        print(f"[WARNING] No source location determined for {item.name}. Skipping LocationStock update.")

                    # 2. Deduct from Global Stock
                    if item.current_stock < quantity:
                         print(f"[WARNING] Insufficient global stock for {item.name}. Available: {item.current_stock}, Required: {quantity}")
                    item.current_stock -= quantity
                    print(f"[DEBUG] Deducted {quantity} {inv_data['unit']} of {item.name}. New global stock: {item.current_stock}")
                    
                    # 3. Create Inventory Transaction
                    transaction = InventoryTransaction(
                        item_id=item_id,
                        transaction_type="transfer", # Issue/Assignment movement
                        quantity=quantity,
                        unit_price=item.unit_price,
                        total_amount=(item.unit_price or 0.0) * quantity,
                        reference_number=f"SVC-ASSIGN-{db_assigned.id}",
                        department=item.category.parent_department if item.category else "Housekeeping",
                        notes=f"Service Assigned: {service.name} - Room: {room.number} - From {source_location.name if source_location else 'Unknown'}",
                        created_by=None,
                        source_location_id=source_location.id if source_location else None,
                        destination_location_id=room.inventory_location_id if room else None,
                        branch_id=db_assigned.branch_id
                    )
                    db.add(transaction)
                    
                    # 4. Create COGS Journal Entry
                    try:
                        db.flush()  # Get transaction ID
                        from app.utils.accounting_helpers import create_consumption_journal_entry
                        cogs_val = quantity * (item.unit_price or 0.0)
                        if cogs_val > 0:
                            create_consumption_journal_entry(
                                db=db,
                                consumption_id=transaction.id,
                                cogs_amount=cogs_val,
                                inventory_item_name=item.name,
                                branch_id=db_assigned.branch_id,
                                created_by=None
                            )

                    except Exception as je_error:
                         print(f"[WARNING] Failed to create COGS journal entry: {je_error}")

                    # 5. Create Employee Inventory Assignment
                    if has_emp_inv_model and EmployeeInventoryAssignment:
                        print(f"[DEBUG] Creating EmployeeInventoryAssignment for item {item.name} (AssignedService {db_assigned.id})")
                        try:
                            emp_inv_assignment = EmployeeInventoryAssignment(
                                employee_id=assigned_dict['employee_id'],
                                assigned_service_id=db_assigned.id,
                                item_id=item_id,
                                quantity_assigned=quantity,
                                quantity_used=0.0,
                                status="assigned", 
                                notes=f"Assigned from {source_location.name if source_location else 'Store'} (LocID: {source_location.id if source_location else '0'})",
                                branch_id=branch_id
                            )
                            db.add(emp_inv_assignment)
                            print(f"[DEBUG] Added EmployeeInventoryAssignment to session")
                        except Exception as create_err:
                            print(f"[ERROR] Failed to init EmployeeInventoryAssignment: {create_err}")
                    else:
                        print(f"[DEBUG] Skipping EmployeeInventoryAssignment (Model missing or flag false)")

            else:
                print(f"[DEBUG] Service has no inventory items, skipping stock deduction")

            print(f"[DEBUG] Committing transaction")
            db.commit()
            print(f"[DEBUG] Transaction committed")
            db.refresh(db_assigned)
            print(f"[DEBUG] AssignedService refreshed, ID={db_assigned.id}")
        except Exception as db_error:
            db.rollback()
            print(f"[ERROR] Database error creating AssignedService: {str(db_error)}")
            import traceback
            print(traceback.format_exc())
            raise
        
        print(f"[DEBUG] AssignedService created with ID: {db_assigned.id}")
        
        # Load relationships for response
        try:
            db_assigned = db.query(AssignedService).options(
                joinedload(AssignedService.service),
                joinedload(AssignedService.employee),
                joinedload(AssignedService.room)
            ).filter(AssignedService.id == db_assigned.id).first()
            
            if not db_assigned:
                raise ValueError("Failed to retrieve created assigned service")
            
            # Verify relationships are loaded
            if not db_assigned.service:
                raise ValueError(f"Service relationship not loaded for service_id={assigned_dict['service_id']}")
            if not db_assigned.employee:
                raise ValueError(f"Employee relationship not loaded for employee_id={assigned_dict['employee_id']}")
            if not db_assigned.room:
                raise ValueError(f"Room relationship not loaded for room_id={assigned_dict['room_id']}")
            
            print(f"[DEBUG] Relationships loaded: service={db_assigned.service.name}, employee={db_assigned.employee.name}, room={db_assigned.room.number}")
            
            # Notify about assignment
            try:
                recipient_id = db_assigned.employee.user_id if db_assigned.employee else None
                notify_service_assigned(db, db_assigned.service.name, db_assigned.employee.name, db_assigned.room.number, db_assigned.id, branch_id=branch_id, recipient_id=recipient_id)
            except Exception as e:
                 print(f"Notification error: {e}")

            return db_assigned
        except Exception as rel_error:
            print(f"[ERROR] Error loading relationships: {str(rel_error)}")
            import traceback
            print(traceback.format_exc())
            # Try to return without relationships as fallback
            db.refresh(db_assigned)
            return db_assigned
    except Exception as e:
        db.rollback()
        import traceback
        error_msg = f"Error creating assigned service: {str(e)}"
        print(f"[ERROR] {error_msg}")
        print(traceback.format_exc())
        raise ValueError(error_msg) from e

def get_assigned_services(db: Session, skip: int = 0, limit: int = 100, employee_id: Optional[int] = None, status: Optional[str] = None, room_id: Optional[int] = None, booking_id: Optional[int] = None, package_booking_id: Optional[int] = None, branch_id: int = None):

    """
    Get assigned services - ultra-simplified version for maximum performance.
    """
    try:
        # Cap limit to prevent performance issues
        if limit > 200:
            limit = 200
        if limit < 1:
            limit = 20
        
        # Start query with minimal eager loading
        query = db.query(AssignedService)
        if branch_id:
            query = query.filter(AssignedService.branch_id == branch_id)
        
        query = query.options(

            joinedload(AssignedService.service),
            joinedload(AssignedService.employee),
            joinedload(AssignedService.room)
        )

        # Apply filters
        if employee_id:
            query = query.filter(AssignedService.employee_id == employee_id)
        
        if status:
            # Handle enum vs string comparison if needed, though SQLAlchemy usually handles it if we pass the string value that matches the enum
            query = query.filter(AssignedService.status == status)

        if room_id:
            query = query.filter(AssignedService.room_id == room_id)
            
        if booking_id:
            query = query.filter(AssignedService.booking_id == booking_id)
            
        if package_booking_id:
            query = query.filter(AssignedService.package_booking_id == package_booking_id)

        # Execute query
        assigned_services = query.order_by(AssignedService.id.desc()).offset(skip).limit(limit).all()
        
        return assigned_services
    except Exception as e:
        import traceback
        print(f"[ERROR] Error in get_assigned_services: {str(e)}")
        print(traceback.format_exc())
        # Return empty list on error to prevent 500
        return []

def update_assigned_service_status(db: Session, assigned_id: int, update_data: AssignedServiceUpdate, updated_by: int = 1, commit: bool = True):
    import traceback
    from app.models.inventory import InventoryItem, InventoryTransaction, Location
    from datetime import timezone, datetime
    
    assigned = db.query(AssignedService).filter(AssignedService.id == assigned_id).first()
    if not assigned:
        return None
    
    # Handle employee reassignment if provided
    if update_data.employee_id is not None:
        employee = db.query(Employee).filter(Employee.id == update_data.employee_id).first()
        if not employee:
            raise ValueError(f"Employee with ID {update_data.employee_id} not found")
        assigned.employee_id = update_data.employee_id
        print(f"[DEBUG] Reassigned service {assigned_id} to employee {employee.name} (ID: {employee.id})")
    
    # Handle status update if provided
    old_status = assigned.status
    new_status = None
    if update_data.status is not None:
        # Handle both enum and string status values
        new_status = update_data.status.value if hasattr(update_data.status, 'value') else str(update_data.status)
        assigned.status = update_data.status
        
        # Track started_at and completed_at
        if new_status == "in_progress" and not assigned.started_at:
            assigned.started_at = datetime.now(timezone.utc)
            print(f"[DEBUG] Set started_at for service {assigned_id}: {assigned.started_at}")
        elif new_status == "completed":
            assigned.completed_at = datetime.now(timezone.utc)
            assigned.last_used_at = assigned.completed_at # Keep legacy field in sync
            print(f"[DEBUG] Set completed_at for service {assigned_id}: {assigned.completed_at}")
    else:
        # If no status update, use current status
        new_status = old_status.value if hasattr(old_status, 'value') else str(old_status)
    
    # Handle billing_status update if provided
    if update_data.billing_status is not None:
        assigned.billing_status = update_data.billing_status
        print(f"[DEBUG] Updated billing_status for service {assigned_id}: {assigned.billing_status}")
    
    # Notify about status change
    if new_status != str(old_status):
        try:
            recipient_id = assigned.employee.user_id if assigned.employee else None
            notify_service_status_changed(db, assigned.service.name, new_status, assigned.id, branch_id=assigned.branch_id, recipient_id=recipient_id)
        except Exception as e:
             print(f"Notification error: {e}")
    if new_status == "completed" and str(old_status) != "completed":
        # Additional logic for completion (e.g. inventory)
        try:
            # Use a nested transaction (savepoint) so that if inventory logic fails,
            # it doesn't abort the main transaction/session.
            with db.begin_nested():
                from app.models.employee_inventory import EmployeeInventoryAssignment
                
                # Mark all inventory assignments for this service as completed (ready for return)
                assignments = db.query(EmployeeInventoryAssignment).filter(
                    EmployeeInventoryAssignment.assigned_service_id == assigned_id,
                    EmployeeInventoryAssignment.status.in_(["assigned", "in_use", "completed"])
                ).all()
                
                for assignment in assignments:
                    assignment.status = "completed"  # Ready for return
                    print(f"[DEBUG] Marked inventory assignment {assignment.id} as completed (ready for return)")
                
                # --- REFACTORED: Unified Inventory Return/Usage Processing ---
                # We process ALL assignments for the service to ensure nothing is missed
                
                # Determine global return location (default)
                global_return_location = None
                if update_data.return_location_id:
                    global_return_location = db.query(Location).filter(Location.id == update_data.return_location_id).first()
                
                if not global_return_location:
                    # Fallback to main warehouse (case-insensitive)
                    global_return_location = db.query(Location).filter(
                        (func.upper(Location.location_type) == "WAREHOUSE") | 
                        (func.upper(Location.location_type) == "CENTRAL_WAREHOUSE") |
                        (Location.is_inventory_point == True)
                    ).filter(Location.branch_id == assigned.branch_id).first()
                    
                    if not global_return_location:
                        global_return_location = db.query(Location).filter(
                            func.upper(Location.location_type).in_(["WAREHOUSE", "CENTRAL_WAREHOUSE", "BRANCH_STORE"]),
                            Location.branch_id == assigned.branch_id
                        ).first()

                # Map provided returns for quick lookup
                returns_map = {}
                if update_data.inventory_returns:
                    for r in update_data.inventory_returns:
                        if hasattr(r, 'assignment_id') and r.assignment_id:
                            returns_map[r.assignment_id] = r
                        elif hasattr(r, 'inventory_item_id') and r.inventory_item_id:
                            returns_map[f"item_{r.inventory_item_id}"] = r

                for assignment in assignments:
                    try:
                        item = assignment.item
                        if not item: continue

                        # 1. Get return data for this assignment (if any)
                        return_data = returns_map.get(assignment.id) or returns_map.get(f"item_{assignment.item_id}")
                        
                        quantity_returned = float(getattr(return_data, 'quantity_returned', 0.0) or 0.0)
                        quantity_used = float(getattr(return_data, 'quantity_used', 0.0) or 0.0)
                        quantity_damaged = float(getattr(return_data, 'quantity_damaged', 0.0) or 0.0)
                        
                        # Auto-infer full usage if NO data provided for this item and it's successful completion
                        if not return_data and quantity_used == 0 and quantity_returned == 0 and quantity_damaged == 0 and new_status == "completed":
                            quantity_used = assignment.balance_quantity
                        
                        print(f"[DEBUG] Processing assignment {assignment.id}: Item={item.name}, Used={quantity_used}, Returned={quantity_returned}, Damaged={quantity_damaged}")

                        # 2. Update assignment record
                        assignment.quantity_used += quantity_used
                        assignment.quantity_returned += quantity_returned
                        
                        # Calculate missing quantity
                        balance = (assignment.quantity_assigned - assignment.quantity_used + quantity_used) - (assignment.quantity_returned + quantity_returned)
                        # Actually simpler: balance = quantity_assigned - used_total - returned_total
                        # But we just did the += updates.
                        current_balance = assignment.quantity_assigned - assignment.quantity_used - assignment.quantity_returned
                        quantity_missing = max(0, current_balance - quantity_damaged)

                        # 3. Handle Used items (Textile vs Consumable)
                        if quantity_used > 0:
                            is_textile = False
                            try:
                                is_textile = (getattr(item, 'track_laundry_cycle', False) or 
                                             (item.category and getattr(item.category, 'track_laundry', False)))
                            except: pass
                                
                            if is_textile:
                                # MOVEMENT TO LAUNDRY
                                laundry_loc = db.query(Location).filter(
                                    ((Location.name.ilike("%Laundry%")) | (Location.location_type == "LAUNDRY")),
                                    Location.branch_id == assigned.branch_id
                                ).first()
                                
                                if not laundry_loc:
                                    print(f"[INFO] Creating missing Laundry location for Branch {assigned.branch_id}")
                                    laundry_loc = Location(
                                        name="Laundry", location_type="LAUNDRY", building="Main", 
                                        room_area="Laundry Area", branch_id=assigned.branch_id, is_inventory_point=True
                                    )
                                    db.add(laundry_loc); db.flush()
                                
                                # Record Laundry Transaction
                                db.add(InventoryTransaction(
                                    item_id=item.id, transaction_type="laundry", quantity=quantity_used,
                                    unit_price=item.unit_price, total_amount=0,
                                    reference_number=f"LNDRY-COL-{assigned_id}", department="Laundry",
                                    destination_location_id=laundry_loc.id,
                                    source_location_id=assigned.room.inventory_location_id if assigned.room else None,
                                    notes=f"Auto-collected Dirty Linen from Room {assigned.room.number if assigned.room else 'Unknown'} (Svc: {assigned.service.name})",
                                    created_by=updated_by, branch_id=assigned.branch_id, created_at=datetime.now(timezone.utc)
                                ))
                                
                                # Add to LaundryLog
                                from app.models.inventory import LaundryLog
                                try:
                                    db.add(LaundryLog(
                                        item_id=item.id, quantity=quantity_used, status="Incomplete Washing",
                                        source_location_id=assigned.room.inventory_location_id if assigned.room else None,
                                        room_number=assigned.room.number if assigned.room else 'Unknown',
                                        notes=f"Auto-collected during service {assigned.service.name}", branch_id=assigned.branch_id
                                    ))
                                except Exception as log_err:
                                    print(f"[WARNING] Failed to add LaundryLog: {log_err}")
                                
                                # Update Stock in Laundry Location
                                from app.models.inventory import LocationStock
                                l_stock = db.query(LocationStock).filter(LocationStock.location_id == laundry_loc.id, LocationStock.item_id == item.id).first()
                                if l_stock: l_stock.quantity += quantity_used
                                else: db.add(LocationStock(location_id=laundry_loc.id, item_id=item.id, quantity=quantity_used, branch_id=assigned.branch_id))
                                
                                item.current_stock += quantity_used
                            else:
                                # REGULAR USAGE
                                db.add(InventoryTransaction(
                                    item_id=item.id, transaction_type="out", quantity=quantity_used,
                                    unit_price=item.unit_price, total_amount=quantity_used * (item.unit_price or 0.0),
                                    reference_number=f"SVC-USAGE-{assigned_id}",
                                    department=item.category.name if item.category else "Housekeeping",
                                    notes=f"Actual Consumption during Service: {assigned.service.name}",
                                    created_by=updated_by, branch_id=assigned.branch_id, created_at=datetime.now(timezone.utc)
                                ))

                        # 4. Handle Clean Returns (Back to Store)
                        if quantity_returned > 0:
                            item.current_stock = (item.current_stock or 0.0) + round(float(quantity_returned), 4)
                            dest_loc = global_return_location
                            if return_data and hasattr(return_data, 'return_location_id') and return_data.return_location_id:
                                spec_loc = db.query(Location).filter(Location.id == return_data.return_location_id).first()
                                if spec_loc: dest_loc = spec_loc
                            
                            if dest_loc:
                                from app.models.inventory import LocationStock
                                lstk = db.query(LocationStock).filter(LocationStock.location_id == dest_loc.id, LocationStock.item_id == item.id).first()
                                if lstk: lstk.quantity += round(quantity_returned, 4)
                                else: db.add(LocationStock(location_id=dest_loc.id, item_id=item.id, quantity=round(quantity_returned, 4), branch_id=assigned.branch_id))

                            db.add(InventoryTransaction(
                                item_id=item.id, transaction_type="transfer_in", quantity=round(quantity_returned, 4),
                                unit_price=item.unit_price, total_amount=0, reference_number=f"SVC-RETURN-{assigned_id}",
                                department="Housekeeping", notes=f"Return to {dest_loc.name if dest_loc else 'Office'}",
                                created_by=updated_by, branch_id=assigned.branch_id
                            ))

                        # 5. Handle Damaged/Missing (Waste Logs)
                        for w_qty, reason in [(quantity_damaged, "Damaged"), (quantity_missing, "Missing")]:
                            if w_qty > 0:
                                waste_data = {"item_id": item.id, "quantity": w_qty, "unit": item.unit or "pcs", "reason_code": reason, "notes": f"Auto-reported during {assigned.service.name}", "location_id": (assigned.room.inventory_location_id if assigned.room else assigned.room_id)}
                                reporter_id = assigned.employee.user_id if assigned.employee and assigned.employee.user_id else 1
                                from app.curd import inventory as crud_inventory
                                try:
                                    crud_inventory.create_waste_log(db, waste_data, reported_by=reporter_id, branch_id=assigned.branch_id)
                                except Exception as waste_err:
                                     print(f"[WARNING] Waste log failure: {waste_err}")

                        # Finalize Status
                        if (assignment.quantity_returned + assignment.quantity_used + quantity_damaged + quantity_missing) >= assignment.quantity_assigned:
                            assignment.is_returned = True; assignment.status = "returned"; assignment.returned_at = datetime.now(timezone.utc)
                        else: assignment.status = "partially_returned"  

                    except Exception as loop_err:
                         print(f"[ERROR] Loop Error in return processing: {str(loop_err)}")
                         import traceback
                         traceback.print_exc()
                
        except ImportError:
            print("[WARNING] EmployeeInventoryAssignment model not found, skipping inventory return processing")
        except Exception as e:
            print(f"[ERROR] Fatal error processing inventory returns: {str(e)}")
            print(traceback.format_exc())
            # Don't fail the status update if return processing fails

    # Sync back to ServiceRequest for ANY status change (Syncing status and billing_status)
    try:
        from app.models.service_request import ServiceRequest
        # Find matching service requests for this room
        requests = db.query(ServiceRequest).filter(
            ServiceRequest.room_id == assigned.room_id,
            ServiceRequest.status.notin_(["cancelled"]) 
        ).all()
        
        print(f"[DEBUG-SYNC] Found {len(requests)} ServiceRequests for Room {assigned.room_id} to Sync (Current Svc Status: {new_status})")
        
        for req in requests:
            # Check if employee matches (if assigned) and if type matches (heuristic)
            employee_match = (req.employee_id == assigned.employee_id or req.employee_id is None)
            type_match = False
            
            req_type = str(req.request_type).lower()
            svc_name = str(assigned.service.name).lower()
            
            if req_type == "cleaning" and any(term in svc_name for term in ["clean", "housekeep", "sweep", "mop"]):
                type_match = True
            elif req_type == "refill" and any(term in svc_name for term in ["refill", "replenish", "stock", "restock"]):
                type_match = True
            elif req_type in ["delivery", "food_delivery", "food"]:
                if req.food_order_id:
                    type_match = True
                elif any(term in svc_name for term in ["food", "delivery", "breakfast", "lunch", "dinner", "milk", "water", "tea", "coffee", "snack", "beverage", "drink"]):
                    type_match = True
            
            # Check if this request was created recently (last 7 days)
            is_recent = True
            if req.created_at:
                is_recent = (datetime.now(timezone.utc) - req.created_at).total_seconds() < 604800 # 7 days
            
            if type_match and is_recent:
                # Sync employee assignment if relevant
                if assigned.employee_id and (req.employee_id is None or req.employee_id != assigned.employee_id):
                    # Only sync if it was unassigned or if we are certain this is the same task
                    # For now, let's just update it if it's currently None
                    if req.employee_id is None:
                        req.employee_id = assigned.employee_id
                        print(f"[DEBUG-SYNC] Syncing Employee {assigned.employee_id} to Req {req.id}")

                # Update status if it's not already completed and we have a new relevant status
                if new_status in ["in_progress", "completed"] and req.status != "completed":
                    if req.status != new_status:
                        print(f"[DEBUG-SYNC] Syncing Req {req.id} status from {req.status} to {new_status}")
                        req.status = new_status
                        if new_status == "in_progress" and not req.started_at:
                            req.started_at = datetime.now(timezone.utc)
                        elif new_status == "completed" and not req.completed_at:
                            req.completed_at = datetime.now(timezone.utc)
                
                # ALWAYS propagate billing_status if we have one (Paid/Unpaid)
                # Priority: 1. Input data 2. Database state (if not default)
                current_billing = update_data.billing_status or (assigned.billing_status if assigned.billing_status != "unbilled" else None)
                
                if current_billing:
                    req.billing_status = current_billing
                    print(f"[DEBUG-SYNC] Syncing Req {req.id} billing to {current_billing}")
                    
                    if req.food_order_id:
                        try:
                            from app.models.foodorder import FoodOrder
                            food_order = db.query(FoodOrder).filter(FoodOrder.id == req.food_order_id).first()
                            if food_order:
                                # Update order status to completed if service is completed
                                if new_status == "completed":
                                    food_order.status = "completed"
                                # Update billing status
                                food_order.billing_status = current_billing
                                print(f"[INFO] Auto-updated FoodOrder {food_order.id} status/billing based on sync")
                        except Exception as fo_err:
                            print(f"[WARNING] Failed to update linked FoodOrder: {fo_err}")
            
    except Exception as sync_err:
        print(f"[WARNING] Status sync to ServiceRequest failed: {sync_err}")
        import traceback
        traceback.print_exc()
    
    if commit:
        db.commit()
    else:
        db.flush()
    
    print(f"[DEBUG] Finished update_assigned_service_status for {assigned_id}. Final Status: {assigned.status}, Billing: {assigned.billing_status}")
    db.refresh(assigned)
    return assigned

def delete_assigned_service(db: Session, assigned_id: int):
    assigned = db.query(AssignedService).filter(AssignedService.id == assigned_id).first()
    if assigned:
        db.delete(assigned)
        db.commit()
        return True
    return False
