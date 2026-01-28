from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, text
from typing import List, Optional
from datetime import datetime
import os
import shutil
import uuid
import json
from app.schemas import service as service_schema
from app.models.user import User
from app.models.service import Service, AssignedService, service_inventory_item
from app.models.inventory import InventoryItem
from app.curd import service as service_crud
from app.utils.auth import get_db, get_current_user
from app.curd.notification import notify_service_assigned, notify_service_status_changed

router = APIRouter(prefix="/services", tags=["Services"])

UPLOAD_DIR = "uploads/services"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _load_inventory_items_for_service(db: Session, service_id: int):
    """
    Load inventory items for a service. Best effort: return empty list if permission denied.
    """
    items = []
    try:
        print(f"[DEBUG _load_inventory_items_for_service] Loading inventory items for service {service_id}")
        stmt = select(
            service_inventory_item.c.inventory_item_id,
            service_inventory_item.c.quantity
        ).where(service_inventory_item.c.service_id == service_id)
        rows = db.execute(stmt).fetchall()
        print(f"[DEBUG _load_inventory_items_for_service] Found {len(rows)} rows in service_inventory_items table for service {service_id}")
        for row in rows:
            try:
                item_id = getattr(row, "inventory_item_id", None)
                quantity = getattr(row, "quantity", None)
                if item_id is None:
                    item_id = row[0]
                    quantity = row[1]
                inv_item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
                if inv_item:
                    item_data = {
                        "id": int(inv_item.id),
                        "name": str(inv_item.name),
                        "item_code": getattr(inv_item, "item_code", None),
                        "unit": str(getattr(inv_item, "unit", "pcs") or "pcs"),
                        "quantity": float(quantity) if quantity is not None else 1.0,
                        "unit_price": float(inv_item.unit_price) if inv_item.unit_price is not None else 0.0,
                        "selling_price": float(inv_item.selling_price) if hasattr(inv_item, "selling_price") and inv_item.selling_price is not None else None
                    }
                    items.append(item_data)
                    print(f"[DEBUG _load_inventory_items_for_service] Added item: {item_data['name']} (ID: {item_data['id']}, Qty: {item_data['quantity']})")
                else:
                    print(f"[WARNING _load_inventory_items_for_service] Inventory item {item_id} not found in database")
            except Exception as row_err:
                print(f"[WARNING] Failed to process inventory row for service {service_id}: {str(row_err)}")
                continue
    except Exception as e:
        db.rollback()
        print(f"[ERROR _load_inventory_items_for_service] Unable to load inventory items for service {service_id}: {str(e)}")
        import traceback
        print(traceback.format_exc())
    print(f"[DEBUG _load_inventory_items_for_service] Returning {len(items)} inventory items for service {service_id}")
    return items


def _serialize_service(service: Service, db: Session):
    if not service:
        return None

    inventory_items = _load_inventory_items_for_service(db, service.id)
    print(f"[DEBUG _serialize_service] Service {service.id} ({service.name}) has {len(inventory_items)} inventory items")
    
    return {
        "id": int(service.id),
        "name": str(service.name),
        "description": str(service.description) if service.description else None,
        "charges": float(service.charges),
        "is_visible_to_guest": bool(getattr(service, "is_visible_to_guest", False)),
        "average_completion_time": str(service.average_completion_time) if getattr(service, "average_completion_time", None) else None,
        "created_at": service.created_at,
        "images": [
            {"id": int(img.id), "image_url": str(img.image_url)}
            for img in (service.images or [])
        ],
        "inventory_items": inventory_items
    }


def _delete_file(image_url: str):
    try:
        if not image_url:
            return
        relative_path = image_url.lstrip("/")
        absolute_path = os.path.normpath(relative_path)
        if not os.path.isabs(absolute_path):
            absolute_path = os.path.join(os.getcwd(), absolute_path)
        if os.path.exists(absolute_path):
            os.remove(absolute_path)
            print(f"[INFO] Deleted file: {absolute_path}")
    except Exception as cleanup_error:
        print(f"[WARNING] Failed to delete file {image_url}: {cleanup_error}")


# Service CRUD
@router.post("", response_model=service_schema.ServiceOut)
async def create_service(
    name: str = Form(...),
    description: str = Form(...),
    charges: float = Form(...),
    images: List[UploadFile] = File([]),
    inventory_items: Optional[str] = Form(None),  # JSON string of inventory items
    is_visible_to_guest: str = Form("false"),  # Accept as string, convert to bool
    average_completion_time: Optional[str] = Form(None),  # e.g., "30 minutes", "1 hour"
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new service with optional images and inventory items.
    """
    import traceback
    import sys

    is_visible_bool = (
        is_visible_to_guest.lower() in ("true", "1", "yes")
        if isinstance(is_visible_to_guest, str)
        else bool(is_visible_to_guest)
    )

    image_urls = []

    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        if not os.access(UPLOAD_DIR, os.W_OK):
            raise HTTPException(status_code=500, detail=f"Upload directory is not writable: {UPLOAD_DIR}")

        try:
            for img in images:
                if not img.filename:
                    continue

                original_filename = img.filename if img.filename else "image.jpg"
                filename = f"svc_{uuid.uuid4().hex}_{original_filename}"
                file_path = os.path.join(UPLOAD_DIR, filename)

                try:
                    contents = await img.read()
                    with open(file_path, "wb") as buffer:
                        buffer.write(contents)
                except (AttributeError, TypeError):
                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(img.file, buffer)

                if not os.path.exists(file_path):
                    raise HTTPException(status_code=500, detail=f"Failed to save image: {original_filename}")

                normalized_path = file_path.replace("\\", "/")
                image_urls.append(f"/{normalized_path}")
        except HTTPException:
            raise
        except Exception as img_error:
            error_detail = f"Failed to save service images: {str(img_error)}\n{traceback.format_exc()}"
            print(f"[ERROR create_service] {error_detail}")
            sys.stderr.write(f"ERROR in create_service (image upload): {error_detail}\n")
            raise HTTPException(status_code=500, detail=f"Failed to upload images: {str(img_error)}")

        inventory_items_list = None
        if inventory_items:
            try:
                inventory_items_data = json.loads(inventory_items)
                if not isinstance(inventory_items_data, list):
                    raise ValueError("inventory_items must be a JSON array")
                inventory_items_list = [
                    service_schema.ServiceInventoryItemBase(**item)
                    for item in inventory_items_data
                ]
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                error_detail = f"Invalid inventory_items JSON: {str(e)}"
                print(f"[ERROR create_service] {error_detail}")
                raise HTTPException(status_code=400, detail=error_detail)

        try:
            service = service_crud.create_service(
                db,
                name,
                description,
                charges,
                image_urls,
                inventory_items_list,
                is_visible_bool,
                average_completion_time,
            )
        except Exception as db_error:
            error_detail = f"Failed to create service in database: {str(db_error)}\n{traceback.format_exc()}"
            print(f"[ERROR create_service] {error_detail}")
            sys.stderr.write(f"ERROR in create_service (database): {error_detail}\n")
            for img_url in image_urls:
                _delete_file(img_url)
            raise HTTPException(status_code=500, detail=f"Failed to create service: {str(db_error)}")

        service_dict = _serialize_service(service, db)
        print(f"[DEBUG create_service] Created service ID: {service.id}")
        return service_dict

    except HTTPException:
        raise
    except Exception as e:
        error_detail = f"Unexpected error in create_service: {str(e)}\n{traceback.format_exc()}"
        print(f"[ERROR create_service] {error_detail}")
        sys.stderr.write(f"ERROR in create_service: {error_detail}\n")
        raise HTTPException(status_code=500, detail=f"Failed to create service: {str(e)}")


@router.put("/{service_id}", response_model=service_schema.ServiceOut)
async def update_service_endpoint(
    service_id: int,
    name: str = Form(...),
    description: str = Form(...),
    charges: float = Form(...),
    images: List[UploadFile] = File([]),
    inventory_items: Optional[str] = Form(None),
    remove_image_ids: Optional[str] = Form(None),
    is_visible_to_guest: str = Form("false"),
    average_completion_time: Optional[str] = Form(None),  # e.g., "30 minutes", "1 hour"
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing service, allowing image and inventory adjustments."""
    import traceback
    import sys

    is_visible_bool = (
        is_visible_to_guest.lower() in ("true", "1", "yes")
        if isinstance(is_visible_to_guest, str)
        else bool(is_visible_to_guest)
    )

    remove_image_ids_list: List[int] = []
    if remove_image_ids:
        try:
            ids_data = json.loads(remove_image_ids)
            if not isinstance(ids_data, list):
                raise ValueError("remove_image_ids must be a JSON array")
            remove_image_ids_list = [int(img_id) for img_id in ids_data]
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            raise HTTPException(status_code=400, detail=f"Invalid remove_image_ids: {str(e)}")

    inventory_items_list = None
    if inventory_items is not None:
        try:
            items_data = json.loads(inventory_items) if inventory_items else []
            if not isinstance(items_data, list):
                raise ValueError("inventory_items must be a JSON array")
            inventory_items_list = [
                service_schema.ServiceInventoryItemBase(**item) for item in items_data
            ]
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            raise HTTPException(status_code=400, detail=f"Invalid inventory_items JSON: {str(e)}")

    new_image_urls: List[str] = []

    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        if not os.access(UPLOAD_DIR, os.W_OK):
            raise HTTPException(status_code=500, detail=f"Upload directory is not writable: {UPLOAD_DIR}")

        for img in images:
            if not img.filename:
                continue

            original_filename = img.filename if img.filename else "image.jpg"
            filename = f"svc_{uuid.uuid4().hex}_{original_filename}"
            file_path = os.path.join(UPLOAD_DIR, filename)

            try:
                contents = await img.read()
                with open(file_path, "wb") as buffer:
                    buffer.write(contents)
            except (AttributeError, TypeError):
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(img.file, buffer)

            if not os.path.exists(file_path):
                raise HTTPException(status_code=500, detail=f"Failed to save image: {original_filename}")

            normalized_path = file_path.replace("\\", "/")
            new_image_urls.append(f"/{normalized_path}")
    except HTTPException:
        for url in new_image_urls:
            _delete_file(url)
        raise
    except Exception as img_error:
        for url in new_image_urls:
            _delete_file(url)
        error_detail = f"Failed to process images for update: {str(img_error)}\n{traceback.format_exc()}"
        print(f"[ERROR update_service] {error_detail}")
        sys.stderr.write(f"ERROR in update_service (image upload): {error_detail}\n")
        raise HTTPException(status_code=500, detail=f"Failed to upload images: {str(img_error)}")

    try:
        service, removed_image_paths = service_crud.update_service(
            db,
            service_id,
            name,
            description,
            charges,
            new_image_urls,
            remove_image_ids_list,
            inventory_items_list,
            is_visible_bool,
            average_completion_time,
        )
    except ValueError as ve:
        for url in new_image_urls:
            _delete_file(url)
        message = str(ve)
        status = 404 if "not found" in message.lower() else 400
        raise HTTPException(status_code=status, detail=message)
    except Exception as db_error:
        for url in new_image_urls:
            _delete_file(url)
        error_detail = f"Failed to update service: {str(db_error)}\n{traceback.format_exc()}"
        print(f"[ERROR update_service] {error_detail}")
        sys.stderr.write(f"ERROR in update_service (database): {error_detail}\n")
        raise HTTPException(status_code=500, detail=f"Failed to update service: {str(db_error)}")

    for path in removed_image_paths:
        _delete_file(path)

    print(f"[DEBUG update_service] Service {service_id} updated successfully")
    return _serialize_service(service, db)

def _list_services_impl(db: Session, skip: int = 0, limit: int = 20):
    """Helper function for list_services with inventory items and quantities"""
    try:
        # Get services with eager loading
        services = service_crud.get_services(db, skip=skip, limit=limit)
        
        if not services:
            return []
        
        # Manually add inventory items with quantities from association table
        result = []
        for service in services:
            try:
                # Create images list matching ServiceImageOut schema
                images_list = []
                for img in (service.images if service.images else []):
                    images_list.append({
                        "id": int(img.id),
                        "image_url": str(img.image_url)
                    })
                
                service_dict = {
                    "id": int(service.id),
                    "name": str(service.name),
                    "description": str(service.description) if service.description else None,
                    "charges": float(service.charges),
                    "is_visible_to_guest": bool(service.is_visible_to_guest if hasattr(service, 'is_visible_to_guest') else False),
                    "created_at": service.created_at,  # Keep as datetime for Pydantic
                    "images": images_list,
                    "inventory_items": []
                }
                
                # Query association table for quantities
                try:
                    # Query association table directly using column access
                    stmt = select(
                        service_inventory_item.c.inventory_item_id.label('item_id'),
                        service_inventory_item.c.quantity.label('qty')
                    ).where(service_inventory_item.c.service_id == service.id)
                    
                    associations_result = db.execute(stmt)
                    associations = associations_result.fetchall()
                    
                    # Process each association
                    for assoc_row in associations:
                        try:
                            # Access row values - try both attribute and index access
                            if hasattr(assoc_row, 'item_id'):
                                inv_item_id = assoc_row.item_id
                                quantity = assoc_row.qty
                            else:
                                # Fallback to index access
                                inv_item_id = assoc_row[0]
                                quantity = assoc_row[1]
                            
                            # Query inventory item
                            inv_item = db.query(InventoryItem).filter(InventoryItem.id == inv_item_id).first()
                            
                            if inv_item:
                                # Create inventory item dict matching ServiceInventoryItemOut schema exactly
                                inv_item_dict = {
                                    "id": int(inv_item.id),
                                    "name": str(inv_item.name),
                                    "item_code": getattr(inv_item, 'item_code', None),
                                    "unit": str(getattr(inv_item, 'unit', 'pcs') or 'pcs'),
                                    "quantity": float(quantity) if quantity is not None else 1.0,
                                    "unit_price": float(inv_item.unit_price) if inv_item.unit_price is not None else 0.0,
                                    "selling_price": float(inv_item.selling_price) if hasattr(inv_item, 'selling_price') and inv_item.selling_price is not None else None
                                }
                                service_dict["inventory_items"].append(inv_item_dict)
                        except Exception as inv_error:
                            print(f"[WARNING] Error processing inventory item for service {service.id}: {str(inv_error)}")
                            import traceback
                            print(traceback.format_exc())
                            continue
                except Exception as assoc_error:
                    print(f"[WARNING] Error querying inventory associations for service {service.id}: {str(assoc_error)}")
                    import traceback
                    print(traceback.format_exc())
                    # Continue without inventory items
                
                result.append(service_dict)
            except Exception as service_error:
                print(f"[WARNING] Error processing service {service.id if service else 'unknown'}: {str(service_error)}")
                import traceback
                print(traceback.format_exc())
                # Skip this service and continue
                continue
        
        return result
    except Exception as e:
        import traceback
        error_detail = f"Error in _list_services_impl: {str(e)}"
        print(f"[ERROR] {error_detail}")
        print(traceback.format_exc())
        
        # Fallback: return services without inventory items
        try:
            print("[INFO] Attempting fallback: returning services without inventory items")
            services = service_crud.get_services(db, skip=skip, limit=limit)
            fallback_result = []
            for service in services:
                try:
                    fallback_result.append({
                        "id": int(service.id),
                        "name": str(service.name),
                        "description": str(service.description) if service.description else None,
                        "charges": float(service.charges),
                        "is_visible_to_guest": bool(service.is_visible_to_guest if hasattr(service, 'is_visible_to_guest') else False),
                        "created_at": service.created_at,
                        "images": [{"id": int(img.id), "image_url": str(img.image_url)} for img in (service.images if service.images else [])],
                        "inventory_items": []
                    })
                except Exception:
                    continue
            return fallback_result
        except Exception as fallback_error:
            print(f"[ERROR] Fallback also failed: {str(fallback_error)}")
            # Re-raise original error
            raise e

@router.get("", response_model=List[service_schema.ServiceOut])
def list_services(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), skip: int = 0, limit: int = 20):
    try:
        print(f"[DEBUG] list_services called with skip={skip}, limit={limit}")
        
        # Cap limit to prevent performance issues
        if limit > 1000:
            limit = 1000
        if limit < 1:
            limit = 20
        
        # Try the full implementation first
        try:
            result = _list_services_impl(db, skip, limit)
            if result:
                print(f"[DEBUG] Full implementation returned {len(result)} services")
                return result
        except Exception as impl_error:
            print(f"[WARNING] Full implementation failed, trying simple approach: {str(impl_error)}")
            import traceback
            print(traceback.format_exc())
        
        # Fallback: Simple approach - return services directly
        print("[INFO] Using simple fallback: returning services directly")
        services = service_crud.get_services(db, skip=skip, limit=limit)
        
        print(f"[DEBUG] Found {len(services) if services else 0} services from database")
        
        if not services:
            print("[INFO] No services found in database")
            return []
        
        # Build response with inventory items
        result = []
        for service in services:
            try:
                # Get inventory items with quantities
                inventory_items_list = []
                try:
                    stmt = select(
                        service_inventory_item.c.inventory_item_id,
                        service_inventory_item.c.quantity
                    ).where(service_inventory_item.c.service_id == service.id)
                    associations = db.execute(stmt).fetchall()
                    
                    for row in associations:
                        inv_item_id = row[0] if isinstance(row, tuple) else row.inventory_item_id
                        quantity = row[1] if isinstance(row, tuple) else row.quantity
                        
                        inv_item = db.query(InventoryItem).filter(InventoryItem.id == inv_item_id).first()
                        if inv_item:
                            inventory_items_list.append({
                                "id": inv_item.id,
                                "name": inv_item.name,
                                "item_code": getattr(inv_item, 'item_code', None),
                                "unit": getattr(inv_item, 'unit', 'pcs') or 'pcs',
                                "quantity": float(quantity) if quantity is not None else 1.0,
                                "unit_price": float(inv_item.unit_price) if inv_item.unit_price is not None else 0.0,
                                "selling_price": float(inv_item.selling_price) if hasattr(inv_item, 'selling_price') and inv_item.selling_price is not None else None
                            })
                except Exception as inv_error:
                    print(f"[WARNING] Error loading inventory items for service {service.id}: {str(inv_error)}")
                    inventory_items_list = []
                
                # Build service dict - ensure all fields match ServiceOut schema
                service_data = {
                    "id": int(service.id),
                    "name": str(service.name),
                    "description": str(service.description) if service.description else None,
                    "charges": float(service.charges),
                    "is_visible_to_guest": bool(getattr(service, 'is_visible_to_guest', False)),
                    "created_at": service.created_at,  # Keep as datetime object
                    "images": [{"id": int(img.id), "image_url": str(img.image_url)} for img in (service.images or [])],
                    "inventory_items": inventory_items_list
                }
                
                result.append(service_data)
            except Exception as service_error:
                print(f"[WARNING] Error processing service {service.id}: {str(service_error)}")
                continue
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = f"Failed to fetch services: {str(e)}"
        print(f"[ERROR] Error in list_services endpoint: {error_msg}")
        print(traceback.format_exc())
        # Return empty list instead of raising to prevent frontend breakage
        return []

@router.get("/", response_model=List[service_schema.ServiceOut])  # Handle trailing slash
def list_services_slash(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), skip: int = 0, limit: int = 20):
    # Use the same implementation as the main endpoint
    return list_services(db, skip, limit)

@router.delete("/{service_id}")
def delete_service(service_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        image_paths = service_crud.delete_service(db, service_id)
        for path in image_paths:
            _delete_file(path)
        return {"detail": "Deleted successfully"}
    except ValueError as ve:
        message = str(ve)
        status = 404 if "not found" in message.lower() else 400
        raise HTTPException(status_code=status, detail=message)
    except RuntimeError as re:
        raise HTTPException(status_code=500, detail=str(re))
    except Exception as e:
        import traceback
        error_detail = f"Failed to delete service {service_id}: {str(e)}\n{traceback.format_exc()}"
        print(f"[ERROR delete_service] {error_detail}")
        raise HTTPException(status_code=500, detail="Failed to delete service")

# Assigned Services
@router.post("/assign")
def assign_service(
    payload: service_schema.AssignedServiceCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Assign a service to an employee for a specific room.
    If the service has inventory items, they will be automatically deducted from stock.
    """
    try:
        print(f"[DEBUG assign_service] ===== START ======")
        print(f"[DEBUG assign_service] Received payload: service_id={payload.service_id}, employee_id={payload.employee_id}, room_id={payload.room_id}")
        print(f"[DEBUG assign_service] Current user: {current_user.id if current_user else 'None'}")
        
        # Validate payload
        if not payload.service_id:
            raise HTTPException(status_code=400, detail="service_id is required")
        if not payload.employee_id:
            raise HTTPException(status_code=400, detail="employee_id is required")
        if not payload.room_id:
            raise HTTPException(status_code=400, detail="room_id is required")
        
        result = service_crud.create_assigned_service(db, payload)
        db.commit() # Force commit to ensure visibility
        print(f"[DEBUG assign_service] Successfully created assigned service ID: {result.id}")
        
        # Send Notification (best effort)
        try:
            notify_service_assigned(
                db, 
                service_name=result.service.name if result.service else "Unknown Service",
                employee_name=result.employee.name if result.employee else "Unknown Employee", 
                room_number=result.room.number if result.room else "Unknown Room", 
                assigned_id=result.id
            )
        except Exception as notif_error:
            print(f"[WARNING] Failed to send assignment notification: {notif_error}")

        # Manually construct response to avoid serialization issues
        response_data = {
            "id": result.id,
            "service": {
                "id": result.service.id if result.service else None,
                "name": result.service.name if result.service else "Unknown",
                "description": result.service.description if result.service else None,
                "charges": result.service.charges if result.service else 0,
                "is_visible_to_guest": result.service.is_visible_to_guest if result.service else False,
                "created_at": result.service.created_at.isoformat() if result.service and result.service.created_at else None,
                "images": [],
                "inventory_items": []
            },
            "employee": {
                "id": result.employee.id if result.employee else None,
                "name": result.employee.name if result.employee else "Unknown"
            },
            "room": {
                "id": result.room.id if result.room else None,
                "number": result.room.number if result.room else "Unknown"
            },
            "assigned_at": result.assigned_at.isoformat() if result.assigned_at else None,
            "status": result.status.value if hasattr(result.status, 'value') else str(result.status),
            "billing_status": result.billing_status if hasattr(result, 'billing_status') else "unbilled"
        }
        
        print(f"[DEBUG assign_service] ===== SUCCESS ======")
        return response_data
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        # User-friendly validation errors
        import traceback
        print(f"[ERROR assign_service] Validation error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        error_detail = f"Failed to assign service: {str(e)}"
        print(f"[ERROR assign_service] {error_detail}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_detail)

@router.get("/assigned", response_model=List[service_schema.AssignedServiceOut])
def get_all_assigned_services(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user), 
    skip: int = 0, 
    limit: int = 20,
    employee_id: Optional[int] = None,
    status: Optional[str] = None
):
    try:
        # Cap limit to prevent performance issues
        # Optimized for low network
        if limit > 200:
            limit = 200
        if limit < 1:
            limit = 50
        assigned_services = service_crud.get_assigned_services(db, skip=skip, limit=limit, employee_id=employee_id, status=status)
        
        # Manually construct response to ensure proper serialization
        result = []
        for assigned in assigned_services:
            # Ensure all relationships are loaded
            if not assigned.service or not assigned.employee or not assigned.room:
                # Skip incomplete records
                print(f"[WARNING] Skipping assigned service {assigned.id} due to missing relationships")
                continue
            
            # Use status enum directly (Pydantic will handle conversion)
            status_enum = assigned.status
            
            # Load inventory items for the service
            service_inventory_items = _load_inventory_items_for_service(db, assigned.service.id)
            print(f"[DEBUG get_all_assigned_services] Service {assigned.service.id} has {len(service_inventory_items)} inventory items")
            
            # Fetch actual inventory items used from EmployeeInventoryAssignment (includes extra items)
            items_used_list = []
            try:
                from app.models.employee_inventory import EmployeeInventoryAssignment
                from app.models.inventory import InventoryItem
                
                print(f"[DEBUG] Querying EmployeeInventoryAssignment for service search {assigned.id}")
                emp_inv_assignments = db.query(EmployeeInventoryAssignment).filter(
                    EmployeeInventoryAssignment.assigned_service_id == assigned.id
                ).all()
                print(f"[DEBUG] Found {len(emp_inv_assignments)} assignments for service {assigned.id}")
                
                if emp_inv_assignments:
                    for eia in emp_inv_assignments:
                        # Fetch item details (optimize with joinedload if needed, but loop is small)
                        inv_item = db.query(InventoryItem).filter(InventoryItem.id == eia.item_id).first()
                        if inv_item:
                            items_used_list.append({
                                "id": int(inv_item.id),
                                "name": str(inv_item.name),
                                "item_code": getattr(inv_item, 'item_code', None),
                                "unit": getattr(inv_item, 'unit', 'pcs') or 'pcs',
                                "quantity": float(eia.quantity_assigned),
                                "unit_price": float(inv_item.unit_price) if inv_item.unit_price is not None else 0.0,
                                "selling_price": float(inv_item.selling_price) if hasattr(inv_item, 'selling_price') and inv_item.selling_price is not None else None
                            })
                    print(f"[DEBUG] Constructed {len(items_used_list)} items_used_list entries")
            except Exception as e:
                print(f"[WARNING] Failed to fetch inventory items used for assigned service {assigned.id}: {e}")
                import traceback
                traceback.print_exc()
            
            # Fallback to template items if no specific assignment records found
            if not items_used_list:
                print(f"[DEBUG] items_used_list empty, falling back to service_inventory_items ({len(service_inventory_items)} items)")
                items_used_list = service_inventory_items or []
            
            print(f"[DEBUG] Final items_used_list for {assigned.id}: {json.dumps(items_used_list, default=str)}")
            
            result.append({
                "id": assigned.id,
                "service_id": assigned.service.id,  # Add service_id for filtering
                "employee_id": assigned.employee.id,  # Add employee_id for filtering
                "room_id": assigned.room.id,  # Add room_id for filtering
                "service": {
                    "id": assigned.service.id,
                    "name": assigned.service.name,
                    "description": assigned.service.description,
                    "charges": assigned.service.charges,
                    "is_visible_to_guest": assigned.service.is_visible_to_guest if hasattr(assigned.service, 'is_visible_to_guest') else False,
                    "created_at": assigned.service.created_at,
                    "images": [{"id": img.id, "image_url": img.image_url} for img in assigned.service.images] if hasattr(assigned.service, 'images') else [],
                    "inventory_items": service_inventory_items
                },
                "employee": {
                    "id": assigned.employee.id,
                    "name": assigned.employee.name
                },
                "room": {
                    "id": assigned.room.id,
                    "number": assigned.room.number
                },
                "assigned_at": assigned.assigned_at,
                "status": status_enum,
                "last_used_at": assigned.last_used_at,
                "inventory_items_used": items_used_list,
                "debug_items": items_used_list # Bypass schema filtering check
            })
        
        return result
    except Exception as e:
        import traceback
        print(f"[ERROR] Error in get_all_assigned_services endpoint: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch assigned services: {str(e)}")


@router.delete("/clear-all", tags=["Services"])
def clear_all_services(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    TEMPORARY ENDPOINT: Clear all services, assigned services, images, and inventory links.
    Use with caution - this cannot be undone!
    """
    try:
        # Delete in correct order to avoid foreign key violations
        print("[WARNING] Clearing all services and assigned services...")
        
        # 1. Delete assigned services first
        deleted_assigned = db.execute(text("DELETE FROM assigned_services")).rowcount
        print(f"Deleted {deleted_assigned} assigned services")
        
        # 2. Delete service inventory item links
        deleted_inventory = db.execute(text("DELETE FROM service_inventory_items")).rowcount
        print(f"Deleted {deleted_inventory} service inventory item links")
        
        # 3. Delete service images
        deleted_images = db.execute(text("DELETE FROM service_images")).rowcount
        print(f"Deleted {deleted_images} service images")
        
        # 4. Finally delete services
        deleted_services = db.execute(text("DELETE FROM services")).rowcount
        print(f"Deleted {deleted_services} services")
        
        db.commit()
        
        return {
            "detail": "All services and assigned services cleared successfully",
            "deleted": {
                "assigned_services": deleted_assigned,
                "services": deleted_services,
                "service_images": deleted_images,
                "service_inventory_items": deleted_inventory
            }
        }
    except Exception as e:
        db.rollback()
        import traceback
        error_detail = f"Failed to clear services: {str(e)}\n{traceback.format_exc()}"
        print(f"[ERROR] {error_detail}")
        raise HTTPException(status_code=500, detail=f"Failed to clear services: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch assigned services: {str(e)}")

@router.patch("/assigned/{assigned_id}")
def update_assigned_status(
    assigned_id: int,
    status_update: service_schema.AssignedServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        updated_service = service_crud.update_assigned_service_status(db, assigned_id, status_update)
        
        if updated_service and status_update.status:
            # Send Notification if status changed
            try:
                # Ensure relationships are loaded for notification message
                service_name = updated_service.service.name if updated_service.service else "Unknown Service"
                
                notify_service_status_changed(
                    db,
                    service_name=service_name,
                    status=str(updated_service.status),
                    assigned_id=updated_service.id
                )
            except Exception as notif_error:
                print(f"[WARNING] Failed to send status notification: {notif_error}")
        
        return updated_service
    except Exception as e:
        import traceback
        print(f"[ERROR] Error updating assigned service status: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to update service status: {str(e)}")

@router.delete("/assigned/{assigned_id}")
def delete_assigned_service(assigned_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    success = service_crud.delete_assigned_service(db, assigned_id)
    if not success:
        raise HTTPException(status_code=404, detail="Assigned service not found")
    return {"detail": "Deleted successfully"}

# Employee Inventory Management Endpoints
@router.get("/employee-inventory/{employee_id}")
def get_employee_inventory_assignments(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[str] = None
):
    """Get all inventory assignments for an employee"""
    try:
        from app.models.employee_inventory import EmployeeInventoryAssignment
        from app.schemas.employee_inventory import EmployeeInventoryAssignmentOut
        from app.models.inventory import LocationStock, Location
        
        query = db.query(EmployeeInventoryAssignment).filter(
            EmployeeInventoryAssignment.employee_id == employee_id
        )
        
        if status:
            # Support comma-separated status values
            status_list = [s.strip() for s in status.split(',')]
            if len(status_list) > 1:
                query = query.filter(EmployeeInventoryAssignment.status.in_(status_list))
            else:
                query = query.filter(EmployeeInventoryAssignment.status == status_list[0])
        
        assignments = query.options(
            joinedload(EmployeeInventoryAssignment.item),
            joinedload(EmployeeInventoryAssignment.assigned_service).joinedload(AssignedService.service),
            joinedload(EmployeeInventoryAssignment.assigned_service).joinedload(AssignedService.room)
        ).all()
        
        result = []
        for assignment in assignments:
            # Fetch active stock locations
            stock_locations = []
            if assignment.item_id:
                active_stocks = db.query(LocationStock).join(Location).filter(
                    LocationStock.item_id == assignment.item_id,
                    LocationStock.quantity > 0
                ).all()
                
                stock_locations = [
                    {
                        "id": stock.location.id,
                        "name": stock.location.name,
                        "location_code": stock.location.location_code
                    } for stock in active_stocks if stock.location
                ]

            result.append({
                "id": assignment.id,
                "employee_id": assignment.employee_id,
                "assigned_service_id": assignment.assigned_service_id,
                "item_id": assignment.item_id,
                "item": {
                    "id": assignment.item.id if assignment.item else None,
                    "name": assignment.item.name if assignment.item else "Unknown",
                    "item_code": assignment.item.item_code if assignment.item else None,
                    "unit": assignment.item.unit if assignment.item else "pcs",
                    "location": assignment.item.location if assignment.item else None,
                    "stock_locations": stock_locations,
                } if assignment.item else None,
                "item_name": assignment.item.name if assignment.item else "Unknown",
                "item_code": assignment.item.item_code if assignment.item else None,
                "unit": assignment.item.unit if assignment.item else "pcs",
                "quantity_assigned": assignment.quantity_assigned,
                "quantity_used": assignment.quantity_used,
                "quantity_returned": assignment.quantity_returned,
                "balance_quantity": assignment.balance_quantity,
                "status": assignment.status,
                "is_returned": assignment.is_returned,
                "assigned_at": assignment.assigned_at,
                "returned_at": assignment.returned_at,
                "notes": assignment.notes,
                "service_name": assignment.assigned_service.service.name if assignment.assigned_service and assignment.assigned_service.service else None,
                "room_number": assignment.assigned_service.room.number if assignment.assigned_service and assignment.assigned_service.room else None
            })
        
        return result
    except ImportError:
        raise HTTPException(status_code=501, detail="Employee inventory tracking not available")
    except Exception as e:
        import traceback
        print(f"[ERROR] Error fetching employee inventory: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch employee inventory: {str(e)}")

@router.post("/return-inventory")
def return_inventory_items(
    return_data: dict,  # {assignment_id: int, quantity_returned: float, notes: Optional[str]}
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return inventory items to office/warehouse"""
    try:
        from app.models.employee_inventory import EmployeeInventoryAssignment
        from app.models.inventory import InventoryItem, InventoryTransaction, Location
        
        assignment_id = return_data.get("assignment_id")
        quantity_returned = float(return_data.get("quantity_returned", 0))
        notes = return_data.get("notes", "")
        
        if not assignment_id or quantity_returned <= 0:
            raise HTTPException(status_code=400, detail="Invalid return data")
        
        # Get assignment
        assignment = db.query(EmployeeInventoryAssignment).filter(
            EmployeeInventoryAssignment.id == assignment_id
        ).first()
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Inventory assignment not found")
        
        # Check if return quantity is valid
        balance = assignment.balance_quantity
        if quantity_returned > balance:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot return {quantity_returned}. Balance available: {balance}"
            )
        
        # Update assignment
        assignment.quantity_returned += quantity_returned
        if assignment.quantity_returned >= assignment.quantity_assigned:
            assignment.is_returned = True
            assignment.status = "returned"
            assignment.returned_at = datetime.utcnow()
        
        # Find main warehouse location
        main_location = db.query(Location).filter(
            (Location.location_type == "WAREHOUSE") | 
            (Location.location_type == "CENTRAL_WAREHOUSE") |
            (Location.is_inventory_point == True)
        ).first()
        
        if not main_location:
            main_location = db.query(Location).filter(
                Location.location_type.in_(["WAREHOUSE", "CENTRAL_WAREHOUSE", "BRANCH_STORE"])
            ).first()
        
        # Add stock back
        item = db.query(InventoryItem).filter(InventoryItem.id == assignment.item_id).first()
        if item:
            item.current_stock += quantity_returned
            print(f"[DEBUG] Returned {quantity_returned} {item.unit} of {item.name}. New stock: {item.current_stock}")
        
        # Create return transaction
        transaction = InventoryTransaction(
            item_id=assignment.item_id,
            transaction_type="in",
            quantity=quantity_returned,
            unit_price=item.unit_price if item else None,
            total_amount=item.unit_price * quantity_returned if item and item.unit_price else None,
            reference_number=f"RETURN-{assignment_id}",
            notes=f"Return from Employee: {assignment.employee.name if assignment.employee else 'Unknown'} - {notes}",
            created_by=current_user.id if current_user else None
        )
        db.add(transaction)
        
        db.commit()
        db.refresh(assignment)
        
        return {
            "message": "Inventory returned successfully",
            "assignment_id": assignment.id,
            "quantity_returned": quantity_returned,
            "balance_remaining": assignment.balance_quantity
        }
    except HTTPException:
        raise
    except ImportError:
        raise HTTPException(status_code=501, detail="Employee inventory tracking not available")
    except Exception as e:
        db.rollback()
        import traceback
        print(f"[ERROR] Error returning inventory: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to return inventory: {str(e)}")
