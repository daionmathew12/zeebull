from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError # Added import
from typing import List, Optional
import os
import shutil
import uuid
from datetime import datetime
from app.utils.auth import get_db, get_current_user
from app.models.user import User
from app.curd import inventory as inventory_crud
from app.schemas.inventory import (
    InventoryCategoryCreate, InventoryCategoryUpdate, InventoryCategoryOut,
    InventoryItemCreate, InventoryItemUpdate, InventoryItemOut,
    VendorCreate, VendorUpdate, VendorOut,
    PurchaseMasterCreate, PurchaseMasterUpdate, PurchaseMasterOut,
    PurchaseDetailOut, InventoryTransactionOut,
    StockRequisitionCreate, StockRequisitionOut, StockRequisitionUpdate,
    StockIssueCreate, StockIssueOut,
    WasteLogCreate, WasteLogOut,
    LocationCreate, LocationOut,
    AssetMappingCreate, AssetMappingOut, AssetMappingUpdate,
    AssetRegistryCreate, AssetRegistryOut, AssetRegistryUpdate,
    StockAdjustmentCreate,
    LaundryLogCreate, LaundryLogOut, LaundryLogUpdate
)

router = APIRouter(prefix="/inventory", tags=["Inventory"])

UPLOAD_DIR = "uploads/inventory_items"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# Category Endpoints
@router.post("/categories", response_model=InventoryCategoryOut)
def create_category(
    category: InventoryCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return inventory_crud.create_category(db, category)


@router.get("/categories", response_model=List[InventoryCategoryOut])
def get_categories(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return inventory_crud.get_all_categories(db, skip=skip, limit=limit, active_only=active_only)


@router.put("/categories/{category_id}", response_model=InventoryCategoryOut)
def update_category(
    category_id: int,
    category: InventoryCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    updated = inventory_crud.update_category(db, category_id, category)
    if not updated:
        raise HTTPException(status_code=404, detail="Category not found")
    return updated


@router.delete("/categories/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if category exists
    category = inventory_crud.get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if category has active items
    from app.models.inventory import InventoryItem
    items_count = db.query(InventoryItem).filter(InventoryItem.category_id == category_id, InventoryItem.is_active == True).count()
    if items_count > 0:
        raise HTTPException(status_code=400, detail="Cannot delete category with active items")
        
    # Soft delete
    category.is_active = False
    db.commit()
    return {"message": "Category deleted successfully"}


# Item Endpoints
@router.post("/items", response_model=InventoryItemOut)
async def create_item(
    name: str = Form(...),
    item_code: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    category_id: int = Form(...),
    sub_category: Optional[str] = Form(None),
    hsn_code: Optional[str] = Form(None),
    unit: str = Form("pcs"),
    initial_stock: float = Form(0.0),
    min_stock_level: float = Form(0.0),
    max_stock_level: Optional[float] = Form(None),
    unit_price: float = Form(0.0),
    selling_price: Optional[float] = Form(None),
    gst_rate: float = Form(0.0),
    location: Optional[str] = Form(None),
    barcode: Optional[str] = Form(None),
    is_perishable: bool = Form(False),
    track_serial_number: bool = Form(False),
    is_sellable_to_guest: bool = Form(False),
    track_laundry_cycle: bool = Form(False),
    is_asset_fixed: bool = Form(False),
    maintenance_schedule_days: Optional[int] = Form(None),
    complimentary_limit: Optional[int] = Form(None),
    ingredient_yield_percentage: Optional[float] = Form(None),
    preferred_vendor_id: Optional[int] = Form(None),
    vendor_item_code: Optional[str] = Form(None),
    lead_time_days: Optional[int] = Form(None),
    is_active: bool = Form(True),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Verify category exists
        category = inventory_crud.get_category_by_id(db, category_id)
        if not category:
            raise HTTPException(status_code=404, detail=f"Category with id {category_id} not found")
        
        # Handle image upload
        image_path = None
        if image and image.filename:
            filename = f"item_{uuid.uuid4().hex}_{image.filename}"
            file_path = os.path.join(UPLOAD_DIR, filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            image_path = f"uploads/inventory_items/{filename}".replace("\\", "/")
        
        # Create item
        from app.models.inventory import InventoryItem, InventoryTransaction, Location, LocationStock
        
        # Sanitize optional unique fields
        if barcode == "":
            barcode = None
        if vendor_item_code == "":
            vendor_item_code = None
        
        created_item = InventoryItem(
            name=name,
            item_code=item_code,
            description=description,
            category_id=category_id,
            sub_category=sub_category,
            hsn_code=hsn_code,
            unit=unit,
            current_stock=initial_stock if initial_stock > 0 else 0.0,
            min_stock_level=min_stock_level,
            max_stock_level=max_stock_level,
            unit_price=unit_price,
            selling_price=selling_price,
            gst_rate=gst_rate,
            location=location,
            barcode=barcode,
            image_path=image_path,
            is_perishable=is_perishable,
            track_serial_number=track_serial_number,
            is_sellable_to_guest=is_sellable_to_guest,
            track_laundry_cycle=track_laundry_cycle,
            is_asset_fixed=is_asset_fixed,
            maintenance_schedule_days=maintenance_schedule_days,
            complimentary_limit=complimentary_limit,
            ingredient_yield_percentage=ingredient_yield_percentage,
            preferred_vendor_id=preferred_vendor_id,
            vendor_item_code=vendor_item_code,
            lead_time_days=lead_time_days,
            is_active=is_active,
        )
        
        db.add(created_item)
        try:
            db.flush()  # Get the ID
        except IntegrityError as e:
            db.rollback()
            err_msg = str(e)
            if "ix_inventory_items_item_code" in err_msg:
                raise HTTPException(status_code=400, detail="Item Code already exists. Please use a unique code.")
            elif "ix_inventory_items_barcode" in err_msg:
                raise HTTPException(status_code=400, detail="Barcode already exists.")
            elif "ix_inventory_items_name" in err_msg: # Assuming name might be unique too
                 raise HTTPException(status_code=400, detail="Item Name already exists.")
            else:
                print(f"Database Error: {e}")
                raise HTTPException(status_code=400, detail=f"Database error: {err_msg}")
        
        # Create transaction record for initial stock if provided
        if initial_stock and initial_stock > 0:
            transaction = InventoryTransaction(
                item_id=created_item.id,
                transaction_type="adjustment",
                quantity=initial_stock,
                unit_price=unit_price,
                total_amount=initial_stock * unit_price,
                notes="Initial stock",
                created_by=current_user.id
            )
            db.add(transaction)

            # Create LocationStock entry if location is specified
            if location:
                # Try to find location by name (case-insensitive)
                # We need to be careful with exact matches vs partial
                loc_obj = db.query(Location).filter(Location.name.ilike(location.strip())).first()
                
                # If not found directly, try seeing if it matches known patterns or valid locations
                if not loc_obj:
                    # Fallback: Check if user typed something like "General Store" that maps to "Central Warehouse"?
                    # For now, strict match or partial contains might be safer?
                    pass

                if loc_obj:
                    loc_stock = LocationStock(
                        location_id=loc_obj.id,
                        item_id=created_item.id,
                        quantity=initial_stock
                    )
                    db.add(loc_stock)
                else:
                    # Optional: Log warning that location name didn't match any Location ID
                    print(f"Warning: Item created with location '{location}' but no matching Location found in DB.")
        
        db.commit()
        db.refresh(created_item)
        
        # Convert SQLAlchemy model to dict
        item_dict = {
            key: getattr(created_item, key)
            for key in created_item.__table__.columns.keys()
        }
        item_dict["category_name"] = category.name
        item_dict["department"] = category.parent_department  # Add department from category
        item_dict["is_low_stock"] = created_item.current_stock <= created_item.min_stock_level if created_item.min_stock_level else False
        
        return item_dict
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating item: {str(e)}")


@router.get("/items", response_model=List[InventoryItemOut])
def get_items(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Optimized endpoint with eager loading - no N+1 queries"""
    try:
        items = inventory_crud.get_all_items(db, skip=skip, limit=limit, category_id=category_id, active_only=active_only)
        
        # Fetch last purchase prices efficiently
        item_ids = [i.id for i in items]
        last_prices = {}
        if item_ids:
            from app.models.inventory import PurchaseDetail, PurchaseMaster
            # Fetch most recent purchase details for these items
            # statuses: confirmed or received are valid for "last price"
            rows = db.query(PurchaseDetail.item_id, PurchaseDetail.unit_price, PurchaseMaster.purchase_date, PurchaseMaster.vendor_id)\
                .join(PurchaseMaster)\
                .filter(PurchaseDetail.item_id.in_(item_ids))\
                .filter(PurchaseMaster.status.in_(['received', 'confirmed']))\
                .order_by(PurchaseMaster.purchase_date.desc(), PurchaseDetail.id.desc())\
                .all()
            
            # Since we ordered by date desc, the first time we see an item_id, it is the latest
            vendor_ids = set()
            for iid, price, pdate, vid in rows:
                if iid not in last_prices:
                    last_prices[iid] = {
                        "price": float(price) if price else 0.0,
                        "date": pdate,
                        "vendor_id": vid
                    }
                    if vid: vendor_ids.add(vid)
            
            # Fetch vendor names
            vendor_names = {}
            if vendor_ids:
                from app.models.inventory import Vendor
                vendors = db.query(Vendor).filter(Vendor.id.in_(vendor_ids)).all()
                vendor_names = {v.id: v.name for v in vendors}

        result = []
        for item in items:
            # Category is already loaded via eager loading (when configured), no extra query needed
            category = getattr(item, "category", None)
            last_p = last_prices.get(item.id, {})
            item_dict = {
                **item.__dict__,
                "category_name": category.name if category else None,
                "department": category.parent_department if category else None,  # Add department from category
                "is_low_stock": item.current_stock <= item.min_stock_level if item.min_stock_level else False,
                "last_purchase_price": last_p.get("price", 0.0),
                "last_purchase_date": last_p.get("date"),
                "last_vendor_name": vendor_names.get(last_p.get("vendor_id")) if last_p.get("vendor_id") else None
            }
            # Add category object for frontend grouping
            if category:
                item_dict["category"] = {
                    "id": category.id,
                    "name": category.name,
                    "classification": category.classification
                }
            result.append(item_dict)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching items: {str(e)}")


@router.get("/items/{item_id}", response_model=InventoryItemOut)
def get_item(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = inventory_crud.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    category = inventory_crud.get_category_by_id(db, item.category_id)
    return {
        **item.__dict__,
        "category_name": category.name if category else None,
        "department": category.parent_department if category else None,  # Add department from category
        "is_low_stock": item.current_stock <= item.min_stock_level
    }



@router.get("/items/{item_id}/stocks")
def get_item_stocks(item_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get stock distribution for an item across all locations"""
    return inventory_crud.get_item_stocks(db, item_id)


@router.get("/items/{item_id}/comprehensive-details")
def get_item_comprehensive_details(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.inventory import (
        InventoryItem, LocationStock, Location, PurchaseDetail, PurchaseMaster,
        InventoryTransaction, WasteLog
    )
    from sqlalchemy import func

    # 1. Basic Item Details
    item = inventory_crud.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    category = inventory_crud.get_category_by_id(db, item.category_id)
    
    # 2. Location Stocks
    stocks_query = db.query(LocationStock, Location.name, Location.location_type)\
        .join(Location, LocationStock.location_id == Location.id)\
        .filter(LocationStock.item_id == item_id, LocationStock.quantity != 0).all()
        
    location_stocks = []
    for stock, loc_name, loc_type in stocks_query:
        location_stocks.append({
            "location_id": stock.location_id,
            "location_name": loc_name,
            "location_type": loc_type,
            "quantity": float(stock.quantity),
            "last_updated": stock.last_updated
        })

    # 3. Purchase History & Stats
    purchases_query = db.query(PurchaseDetail, PurchaseMaster)\
        .join(PurchaseMaster, PurchaseDetail.purchase_master_id == PurchaseMaster.id)\
        .filter(PurchaseDetail.item_id == item_id, PurchaseMaster.status.in_(['received', 'confirmed']))\
        .order_by(PurchaseMaster.purchase_date.desc()).all()

    total_purchased_qty = 0.0
    total_purchased_val = 0.0
    purchase_history = []
    
    for detail, master in purchases_query:
        qty = float(detail.quantity or 0)
        val = float(detail.total_amount or 0)
        total_purchased_qty += qty
        total_purchased_val += val
        
        # Get vendor name safely
        vendor_name = master.vendor.name if master.vendor else "Unknown"
        
        purchase_history.append({
            "date": master.purchase_date,
            "purchase_number": master.purchase_number,
            "vendor_name": vendor_name,
            "quantity": qty,
            "unit_price": float(detail.unit_price or 0),
            "total_amount": val
        })

    avg_purchase_price = (total_purchased_val / total_purchased_qty) if total_purchased_qty > 0 else 0.0

    # 4. Usage (Consumption) History & Stats (Transactions type='out', Ref starts with ISS)
    usage_query = db.query(InventoryTransaction)\
        .filter(
            InventoryTransaction.item_id == item_id, 
            InventoryTransaction.transaction_type == 'out',
            InventoryTransaction.reference_number.like('ISS-%')
        ).order_by(InventoryTransaction.created_at.desc()).all()

    total_consumed_qty = 0.0
    total_consumed_val = 0.0
    usage_history = []
    
    for trans in usage_query:
        qty = float(trans.quantity or 0)
        val = float(trans.total_amount or 0)
        total_consumed_qty += qty
        total_consumed_val += val
        
        usage_history.append({
            "date": trans.created_at,
            "reference": trans.reference_number,
            "quantity": qty,
            "notes": trans.notes or "Consumption"
        })

    # 5. Wastage History & Stats
    waste_query = db.query(WasteLog, Location.name)\
        .outerjoin(Location, WasteLog.location_id == Location.id)\
        .filter(WasteLog.item_id == item_id)\
        .order_by(WasteLog.waste_date.desc()).all()
        
    total_wasted_qty = 0.0
    waste_history = []
    
    for log, loc_name in waste_query:
        qty = float(log.quantity or 0)
        total_wasted_qty += qty
        
        waste_history.append({
            "date": log.waste_date,
            "reference": log.log_number,
            "location": loc_name or "Unknown",
            "quantity": qty,
            "reason": log.reason_code,
            "notes": log.notes
        })

    # Calculate wastage value from transactions
    waste_trans_query = db.query(func.sum(InventoryTransaction.total_amount))\
        .filter(
            InventoryTransaction.item_id == item_id,
            InventoryTransaction.transaction_type == 'out',
            InventoryTransaction.reference_number.like('WASTE-%')
        ).scalar()
    total_wasted_val = float(waste_trans_query or 0)

    # 6. Transfers (Stock Movement)
    transfer_query = db.query(InventoryTransaction)\
        .filter(
            InventoryTransaction.item_id == item_id,
            InventoryTransaction.transaction_type.in_(['transfer_out', 'transfer_in'])
        ).order_by(InventoryTransaction.created_at.desc()).all()
        
    transfer_history = []
    for trans in transfer_query:
        transfer_history.append({
            "date": trans.created_at,
            "type": trans.transaction_type,
            "reference": trans.reference_number,
            "quantity": float(trans.quantity or 0),
            "department": trans.department,
            "notes": trans.notes
        })

    # Convert item to dict handling SQLAlchemy internal state
    item_dict = {c.name: getattr(item, c.name) for c in item.__table__.columns}
    item_dict["category_name"] = category.name if category else None

    return {
        "item": item_dict,
        "location_stocks": location_stocks,
        "stats": {
            "total_purchased_qty": total_purchased_qty,
            "total_purchased_val": total_purchased_val,
            "avg_purchase_price": avg_purchase_price,
            "total_consumed_qty": total_consumed_qty,
            "total_consumed_val": total_consumed_val,
            "total_wasted_qty": total_wasted_qty,
            "total_wasted_val": total_wasted_val,
        },
        "history": {
            "purchases": purchase_history,
            "usage": usage_history,
            "wastage": waste_history,
            "transfers": transfer_history
        }
    }


@router.put("/items/{item_id}", response_model=InventoryItemOut)
async def update_item(
    item_id: int,
    name: Optional[str] = Form(None),
    item_code: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    category_id: Optional[int] = Form(None),
    sub_category: Optional[str] = Form(None),
    hsn_code: Optional[str] = Form(None),
    unit: Optional[str] = Form(None),
    min_stock_level: Optional[float] = Form(None),
    max_stock_level: Optional[float] = Form(None),
    unit_price: Optional[float] = Form(None),
    selling_price: Optional[float] = Form(None),
    gst_rate: Optional[float] = Form(None),
    location: Optional[str] = Form(None),
    barcode: Optional[str] = Form(None),
    is_perishable: Optional[bool] = Form(None),
    track_serial_number: Optional[bool] = Form(None),
    is_sellable_to_guest: Optional[bool] = Form(None),
    track_laundry_cycle: Optional[bool] = Form(None),
    is_asset_fixed: Optional[bool] = Form(None),
    maintenance_schedule_days: Optional[int] = Form(None),
    complimentary_limit: Optional[int] = Form(None),
    ingredient_yield_percentage: Optional[float] = Form(None),
    preferred_vendor_id: Optional[int] = Form(None),
    vendor_item_code: Optional[str] = Form(None),
    lead_time_days: Optional[int] = Form(None),
    is_active: Optional[bool] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Handle image upload if provided
        image_path = None
        if image and image.filename:
            filename = f"item_{uuid.uuid4().hex}_{image.filename}"
            file_path = os.path.join(UPLOAD_DIR, filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            image_path = f"uploads/inventory_items/{filename}".replace("\\", "/")
        
        # Sanitize optional unique fields
        if barcode == "" or (isinstance(barcode, str) and barcode.lower() == "null"):
            barcode = None
        if vendor_item_code == "" or (isinstance(vendor_item_code, str) and vendor_item_code.lower() == "null"):
            vendor_item_code = None
        if item_code == "" or (isinstance(item_code, str) and item_code.lower() == "null"):
            item_code = None
        
        # Construct update data
        update_data = InventoryItemUpdate(
            name=name,
            item_code=item_code,
            description=description,
            category_id=category_id,
            sub_category=sub_category,
            hsn_code=hsn_code,
            unit=unit,
            min_stock_level=min_stock_level,
            max_stock_level=max_stock_level,
            unit_price=unit_price,
            selling_price=selling_price,
            gst_rate=gst_rate,
            location=location,
            barcode=barcode,
            image_path=image_path,
            is_perishable=is_perishable,
            track_serial_number=track_serial_number,
            is_sellable_to_guest=is_sellable_to_guest,
            track_laundry_cycle=track_laundry_cycle,
            is_asset_fixed=is_asset_fixed,
            maintenance_schedule_days=maintenance_schedule_days,
            complimentary_limit=complimentary_limit,
            ingredient_yield_percentage=ingredient_yield_percentage,
            preferred_vendor_id=preferred_vendor_id,
            vendor_item_code=vendor_item_code,
            lead_time_days=lead_time_days,
            is_active=is_active
        )
        
        updated = inventory_crud.update_item(db, item_id, update_data)
        if not updated:
            raise HTTPException(status_code=404, detail="Item not found")
            
        # Get category for response
        category = inventory_crud.get_category_by_id(db, updated.category_id)
        
        return {
            **updated.__dict__,
            "category_name": category.name if category else None,
            "department": category.parent_department if category else None,
            "is_low_stock": updated.current_stock <= updated.min_stock_level if updated.min_stock_level else False
        }
    except IntegrityError as e:
        db.rollback()
        err_msg = str(e)
        if "ix_inventory_items_item_code" in err_msg:
            raise HTTPException(status_code=400, detail="Item Code already exists.")
        elif "ix_inventory_items_barcode" in err_msg:
            raise HTTPException(status_code=400, detail="Barcode already exists.")
        elif "ix_inventory_items_name" in err_msg:
            raise HTTPException(status_code=400, detail="Item Name already exists.")
        else:
             raise HTTPException(status_code=400, detail=f"Database integrity error: {err_msg}")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error updating item: {str(e)}")


@router.delete("/items/{item_id}")
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        item = inventory_crud.get_item_by_id(db, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # Always soft delete
        item.is_active = False
        db.commit()
        return {"message": "Item deleted successfully"}
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error deleting item: {str(e)}")


# Vendor Endpoints
@router.post("/vendors", response_model=VendorOut)
def create_vendor(
    vendor: VendorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return inventory_crud.create_vendor(db, vendor)


@router.get("/vendors", response_model=List[VendorOut])
def get_vendors(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return inventory_crud.get_all_vendors(db, skip=skip, limit=limit, active_only=active_only)


@router.get("/vendors/{vendor_id}", response_model=VendorOut)
def get_vendor(vendor_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    vendor = inventory_crud.get_vendor_by_id(db, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


@router.put("/vendors/{vendor_id}", response_model=VendorOut)
def update_vendor(
    vendor_id: int,
    vendor_update: VendorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    vendor = inventory_crud.get_vendor_by_id(db, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    for field, value in vendor_update.dict(exclude_unset=True).items():
        setattr(vendor, field, value)
    
    db.commit()
    db.refresh(vendor)
    return vendor


# Purchase Master Endpoints
@router.post("/purchases", response_model=PurchaseMasterOut)
def create_purchase(
    purchase: PurchaseMasterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Debug logging to file
    import datetime
    with open("purchase_debug.log", "a") as f:
        f.write(f"\n=== {datetime.datetime.now()} ===\n")
        f.write(f"[DEBUG CREATE_PURCHASE] Received purchase data:\n")
        f.write(f"  Status: {purchase.status}\n")
        f.write(f"  Destination Location ID: {purchase.destination_location_id}\n")
        f.write(f"  Details count: {len(purchase.details)}\n")
    
    print(f"[DEBUG CREATE_PURCHASE] Received purchase data:")
    print(f"  Status: {purchase.status}")
    print(f"  Destination Location ID: {purchase.destination_location_id}")
    print(f"  Details count: {len(purchase.details)}")
    
    created = inventory_crud.create_purchase_master(db, purchase, created_by=current_user.id)
    
    # Use centralized status update logic to handle inventory and prices
    # This avoids redundant logic and ensures atomicity
    if purchase.status.lower() == "received":
        # Validate and ensure destination location is set
        if not created.destination_location_id:
            from app.models.inventory import Location
            # Try to find a default warehouse location
            default_location = db.query(Location).filter(
                Location.location_type.in_(["WAREHOUSE", "CENTRAL_WAREHOUSE", "BRANCH_STORE"])
            ).first()
            
            if not default_location:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot receive purchase without a destination location. Please create a warehouse location first or specify one in the purchase."
                )
            
            # Auto-assign the default location
            created.destination_location_id = default_location.id
            db.commit()
            print(f"[AUTO-ASSIGN] No destination location specified. Using default warehouse: {default_location.name}")
        
        # Trigger the centralized status update logic (this handles WAC, stock, and transactions)
        # We temporarily set status to draft in DB if it was created as received to trigger the transition
        if created.status.lower() == "received":
            created.status = "draft"
            db.commit()
            
        created = inventory_crud.update_purchase_status(db, created.id, "received")
    elif purchase.status.lower() != "draft":
        # For other statuses like 'confirmed', just update it
        created = inventory_crud.update_purchase_status(db, created.id, purchase.status)
    
    # Automatically create journal entry for purchase (Scenario 1)
    # Only create if purchase is confirmed/received (not draft)
    if purchase.status.lower() in ["confirmed", "received"]:
        try:
            from app.utils.accounting_helpers import create_purchase_journal_entry
            from app.models.inventory import Vendor
            from app.api.gst_reports import RESORT_STATE_CODE
            
            vendor = inventory_crud.get_vendor_by_id(db, created.vendor_id)
            vendor_name = (vendor.legal_name or vendor.name) if vendor else "Unknown"
            
            # Determine if inter-state purchase
            is_interstate = False
            if vendor and vendor.gst_number and len(vendor.gst_number) >= 2:
                vendor_state_code = vendor.gst_number[:2]
                is_interstate = vendor_state_code != RESORT_STATE_CODE
            
            # Calculate inventory amount (sub_total) and tax amounts
            inventory_amount = float(created.sub_total or 0)
            cgst_amount = float(created.cgst or 0)
            sgst_amount = float(created.sgst or 0)
            igst_amount = float(created.igst or 0)
            
            # Create journal entry
            create_purchase_journal_entry(
                db=db,
                purchase_id=created.id,
                vendor_id=created.vendor_id,
                inventory_amount=inventory_amount,
                cgst_amount=cgst_amount,
                sgst_amount=sgst_amount,
                igst_amount=igst_amount,
                vendor_name=vendor_name,
                is_interstate=is_interstate,
                created_by=current_user.id
            )
        except Exception as e:
            # Log error but don't fail purchase creation
            import traceback
            print(f"Warning: Could not create journal entry for purchase {created.id}: {str(e)}\\n{traceback.format_exc()}")
    
    # Optimized: Batch load items to avoid N+1 queries
    from sqlalchemy.orm import joinedload
    db.refresh(created, ["details"])
    detail_item_ids = [d.item_id for d in created.details if d.item_id]
    items_map = {}
    if detail_item_ids:
        from app.models.inventory import InventoryItem
        items = db.query(InventoryItem).filter(InventoryItem.id.in_(detail_item_ids)).all()
        items_map = {item.id: item for item in items}
    
    # Load vendor
    vendor = inventory_crud.get_vendor_by_id(db, created.vendor_id)
    
    # Build details with item names from map
    details = []
    for detail in created.details:
        item = items_map.get(detail.item_id) if detail.item_id else None
        details.append({
            **detail.__dict__,
            "item_name": item.name if item else None
        })
    
    return {
        **created.__dict__,
        "vendor_name": vendor.name if vendor else None,
        "vendor_gst": vendor.gst_number if vendor else None,
        "created_by_name": current_user.name if current_user else None,
        "details": details
    }


@router.get("/purchases", response_model=List[PurchaseMasterOut])
def get_purchases(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Optimized with eager loading - no N+1 queries"""
    purchases = inventory_crud.get_all_purchases(db, skip=skip, limit=limit, status=status)
    result = []
    for purchase in purchases:
        # Vendor and details.items already loaded via eager loading
        vendor = purchase.vendor
        details = []
        for detail in purchase.details:
            item = detail.item  # Already loaded
            details.append({
                **detail.__dict__,
                "item_name": item.name if item else None
            })
        # Get user separately (not in relationship, but only once per purchase)
        user = db.query(User).filter(User.id == purchase.created_by).first()
        # Get destination location if set
        location_name = None
        if purchase.destination_location_id:
            from app.models.inventory import Location
            location = db.query(Location).filter(Location.id == purchase.destination_location_id).first()
            if location:
                location_name = location.name or f"{location.building} - {location.room_area}"
        result.append({
            **purchase.__dict__,
            "vendor_name": vendor.name if vendor else None,
            "vendor_gst": vendor.gst_number if vendor else None,
            "created_by_name": user.name if user else None,
            "destination_location_name": location_name,
            "details": details
        })
    return result


@router.get("/purchases/{purchase_id}", response_model=PurchaseMasterOut)
def get_purchase(purchase_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    purchase = inventory_crud.get_purchase_by_id(db, purchase_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    # Optimized: Batch load to avoid N+1 queries
    vendor = inventory_crud.get_vendor_by_id(db, purchase.vendor_id)
    user = db.query(User).filter(User.id == purchase.created_by).first()
    
    # Batch load items
    detail_item_ids = [d.item_id for d in purchase.details if d.item_id]
    items_map = {}
    if detail_item_ids:
        from app.models.inventory import InventoryItem
        items = db.query(InventoryItem).filter(InventoryItem.id.in_(detail_item_ids)).all()
        items_map = {item.id: item for item in items}
    
    details = []
    for detail in purchase.details:
        item = items_map.get(detail.item_id) if detail.item_id else None
        details.append({
            **detail.__dict__,
            "item_name": item.name if item else None
        })
    
    # Get destination location name
    location_name = None
    if purchase.destination_location_id:
        from app.models.inventory import Location
        location = db.query(Location).filter(Location.id == purchase.destination_location_id).first()
        if location:
            location_name = location.name or f"{location.building} - {location.room_area}"
    
    return {
        **purchase.__dict__,
        "vendor_name": vendor.name if vendor else None,
        "vendor_gst": vendor.gst_number if vendor else None,
        "created_by_name": user.name if user else None,
        "destination_location_name": location_name,
        "details": details
    }


@router.put("/purchases/{purchase_id}", response_model=PurchaseMasterOut)
def update_purchase(
    purchase_id: int,
    purchase_update: PurchaseMasterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.inventory import InventoryItem, InventoryTransaction, LocationStock
    
    purchase = inventory_crud.get_purchase_by_id(db, purchase_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    old_status = purchase.status
    new_status = purchase_update.status if purchase_update.status is not None else old_status
    
    updated = inventory_crud.update_purchase_master(db, purchase_id, purchase_update)
    if not updated:
        raise HTTPException(status_code=400, detail="Cannot update purchase")
    
    # CASE 1: Purchase RECEIVED
    # Safely handle None values before calling .lower()
    new_status_lower = new_status.lower() if new_status else ""
    old_status_lower = old_status.lower() if old_status else ""
    
    if new_status_lower == "received" and old_status_lower != "received":
        # Validate and ensure destination location is set
        if not updated.destination_location_id:
            from app.models.inventory import Location
            # Try to find a default warehouse location
            default_location = db.query(Location).filter(
                Location.location_type.in_(["WAREHOUSE", "CENTRAL_WAREHOUSE", "BRANCH_STORE"])
            ).first()
            
            if not default_location:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot receive purchase without a destination location. Please create a warehouse location first or specify one in the purchase."
                )
            
            # Auto-assign the default location
            updated.destination_location_id = default_location.id
            db.commit()
            print(f"[AUTO-ASSIGN] No destination location specified. Using default warehouse: {default_location.name}")
        
        for detail in updated.details:
            if not detail.item_id:
                continue
            
            # Use central WAC helper from CRUD
            inventory_crud.update_item_cost_wac(
                db, 
                detail.item_id, 
                float(detail.quantity or 0), 
                float(detail.unit_price or 0)
            )
            
            # Location stock
            if updated.destination_location_id:
                location_stock = db.query(LocationStock).filter(
                    LocationStock.location_id == updated.destination_location_id,
                    LocationStock.item_id == detail.item_id
                ).first()
                
                if location_stock:
                    location_stock.quantity += float(detail.quantity or 0)
                else:
                    location_stock = LocationStock(
                        location_id=updated.destination_location_id,
                        item_id=detail.item_id,
                        quantity=detail.quantity
                    )
                    db.add(location_stock)
            
            # Transaction
            u_price = float(detail.unit_price or 0)
            qty = float(detail.quantity or 0)
            
            transaction = InventoryTransaction(
                item_id=detail.item_id,
                transaction_type="in",
                quantity=qty,
                unit_price=u_price,
                total_amount=u_price * qty,
                reference_number=updated.purchase_number,
                notes=f"Purchase received: {updated.purchase_number}",
                created_by=current_user.id
            )
            db.add(transaction)
    
    # CASE 2: Purchase CANCELLED
    elif new_status.lower() == "cancelled" and old_status.lower() == "received":
        for detail in updated.details:
            if not detail.item_id:
                continue
            
            # Use central WAC helper from CRUD with is_cancellation=True
            inventory_crud.update_item_cost_wac(
                db, 
                detail.item_id, 
                float(detail.quantity or 0), 
                float(detail.unit_price or 0),
                is_cancellation=True
            )
            
            if updated.destination_location_id:
                location_stock = db.query(LocationStock).filter(
                    LocationStock.location_id == updated.destination_location_id,
                    LocationStock.item_id == detail.item_id
                ).first()
                
                if location_stock:
                    location_stock.quantity -= float(detail.quantity or 0)
                    if location_stock.quantity <= 0:
                        db.delete(location_stock)
            
            transaction = InventoryTransaction(
                item_id=detail.item_id,
                transaction_type="out",
                quantity=float(detail.quantity or 0),
                unit_price=float(detail.unit_price or 0),
                total_amount=float(detail.unit_price or 0) * float(detail.quantity or 0),
                reference_number=updated.purchase_number,
                notes=f"Purchase cancelled: {updated.purchase_number}",
                created_by=current_user.id
            )

            db.add(transaction)
            
        # Automatically create journal entry (if not exists)
        try:
            from app.models.account import JournalEntry
            from app.utils.accounting_helpers import create_purchase_journal_entry
            from app.api.gst_reports import RESORT_STATE_CODE
            
            # Check if entry already exists
            existing_entry = db.query(JournalEntry).filter(
                JournalEntry.reference_type == "purchase",
                JournalEntry.reference_id == purchase_id
            ).first()
            
            if not existing_entry:
                vendor = inventory_crud.get_vendor_by_id(db, updated.vendor_id)
                vendor_name = (vendor.legal_name or vendor.name) if vendor else "Unknown"
                
                # Determine if inter-state purchase
                is_interstate = False
                if vendor and vendor.gst_number and len(vendor.gst_number) >= 2:
                    vendor_state_code = vendor.gst_number[:2]
                    is_interstate = vendor_state_code != RESORT_STATE_CODE
                
                # Calculate inventory amount (sub_total) and tax amounts
                inventory_amount = float(updated.sub_total or 0)
                cgst_amount = float(updated.cgst or 0)
                sgst_amount = float(updated.sgst or 0)
                igst_amount = float(updated.igst or 0)
                
                # Create journal entry
                create_purchase_journal_entry(
                    db=db,
                    purchase_id=updated.id,
                    vendor_id=updated.vendor_id,
                    inventory_amount=inventory_amount,
                    cgst_amount=cgst_amount,
                    sgst_amount=sgst_amount,
                    igst_amount=igst_amount,
                    vendor_name=vendor_name,
                    is_interstate=is_interstate,
                    created_by=current_user.id
                )
                print(f"[INFO] Created missing journal entry for purchase #{updated.id}")
        except Exception as e:
            print(f"[WARNING] Could not create journal entry on update: {str(e)}")
    
    db.commit()
    return get_purchase(purchase_id, db, current_user)


@router.delete("/purchases/{purchase_id}")
def delete_purchase(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    purchase = inventory_crud.get_purchase_by_id(db, purchase_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    # Only allow deleting draft purchases
    if purchase.status not in ["draft", "cancelled"]:
        raise HTTPException(status_code=400, detail="Cannot delete purchase that is not draft or cancelled")
    
    # Delete details first
    from app.models.inventory import PurchaseDetail
    db.query(PurchaseDetail).filter(PurchaseDetail.purchase_master_id == purchase_id).delete()
    
    db.delete(purchase)
    db.commit()
    return {"message": "Purchase deleted successfully"}


@router.post("/purchases/{purchase_id}/payments")
def create_purchase_payment(
    purchase_id: int,
    payment_data: dict,  # {amount: float, payment_method: str, notes: str}
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Record a payment for a purchase (Vendor Payment)"""
    purchase = inventory_crud.get_purchase_by_id(db, purchase_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    try:
        amount = float(payment_data.get("amount", 0))
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Invalid amount")
            
        payment_method = payment_data.get("payment_method", "Bank Transfer")
        notes = payment_data.get("notes", "")
        
        # Create Journal Entry
        # Debit: Accounts Payable (Vendor)
        # Credit: Bank/Cash
        
        from app.utils.accounting_helpers import find_ledger_by_name, create_journal_entry
        from app.schemas.account import JournalEntryCreate, JournalEntryLineCreateInEntry
        
        vendor_payable = find_ledger_by_name(db, "Accounts Payable (Vendor)", "Purchase")
        
        # Determine credit ledger
        if payment_method.lower() in ["cash"]:
            credit_ledger = find_ledger_by_name(db, "Cash in Hand", "Asset")
        else:
            credit_ledger = find_ledger_by_name(db, "Bank Account (HDFC)", "Asset") or find_ledger_by_name(db, "Bank Account", "Asset")
            
        if not all([vendor_payable, credit_ledger]):
             raise HTTPException(status_code=400, detail="Required ledgers not found in Chart of Accounts")
             
        lines = [
            JournalEntryLineCreateInEntry(
                debit_ledger_id=vendor_payable.id,
                credit_ledger_id=None,
                amount=amount,
                description=f"Payment for Purchase #{purchase.purchase_number}"
            ),
            JournalEntryLineCreateInEntry(
                debit_ledger_id=None,
                credit_ledger_id=credit_ledger.id,
                amount=amount,
                description=f"Payment to {purchase.vendor.name if purchase.vendor else 'Vendor'}"
            )
        ]
        
        entry = JournalEntryCreate(
            entry_date=datetime.utcnow(),
            reference_type="purchase_payment",
            reference_id=purchase.id,
            description=f"Vendor Payment - {purchase.purchase_number}",
            notes=f"Method: {payment_method}. {notes}",
            lines=lines
        )
        
        journal_entry = create_journal_entry(db, entry, current_user.id)
        
        # Update purchase payment status
        # This is a simplified logic; ideally we sum up all payments
        if amount >= float(purchase.total_amount):
            purchase.payment_status = "paid"
        else:
            purchase.payment_status = "partial"
            
        db.commit()
        
        return {"message": "Payment recorded successfully", "journal_entry_id": journal_entry.id, "payment_status": purchase.payment_status}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error recording payment: {str(e)}")


@router.patch("/purchases/{purchase_id}/status")
def update_purchase_status(
    purchase_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    purchase = inventory_crud.update_purchase_status(db, purchase_id, status)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
        
    # Note: inventory_crud.update_purchase_status already handles 
    # Weighted Average Cost and price updates internally when status is 'received'.
    # Manual price update here is redundant and removed to prevent session synchronization issues.
            
    return {"message": "Purchase status updated successfully", "status": purchase.status}


@router.patch("/purchases/{purchase_id}/payment-status")
def update_purchase_payment_status(
    purchase_id: int,
    payment_status: str,
    payment_method: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update payment status and payment method for a purchase order"""
    purchase = inventory_crud.get_purchase_by_id(db, purchase_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    # Check if payment_status is None or empty
    if not payment_status or payment_status.strip() == "":
        raise HTTPException(status_code=400, detail="Payment status is required")
    
    # Normalize payment status to lowercase for comparison
    payment_status_lower = payment_status.strip().lower()
    
    # Validate payment status
    valid_statuses = ["pending", "partial", "paid"]
    if payment_status_lower not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid payment status. Must be one of: {', '.join(valid_statuses)}")
    
    # Update payment status
    purchase.payment_status = payment_status_lower
    
    # Update payment method if provided (handle None and empty strings)
    if payment_method and payment_method.strip():
        purchase.payment_method = payment_method.strip().lower()
    
    try:
        db.commit()
        db.refresh(purchase)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update payment status: {str(e)}")
    
    return {
        "message": "Payment status updated successfully",
        "payment_status": purchase.payment_status,
        "payment_method": purchase.payment_method
    }


# Transaction Endpoints
@router.get("/transactions", response_model=List[InventoryTransactionOut])
def get_transactions(
    skip: int = 0,
    limit: int = 100,
    item_id: Optional[int] = None,
    # New Filters
    type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Optimized with eager loading - no N+1 queries"""
    from app.models.inventory import InventoryTransaction, StockIssue, InventoryItem, InventoryCategory
    from sqlalchemy.orm import joinedload
    from sqlalchemy import or_

    query = db.query(InventoryTransaction).join(InventoryItem).options(
        joinedload(InventoryTransaction.item),
        joinedload(InventoryTransaction.user)
    )
    
    if item_id:
        query = query.filter(InventoryTransaction.item_id == item_id)
        
    # Filter by Type
    if type and type != "all":
        if type == "initial_stock":
             # Special logic for initial stock
             query = query.filter(
                 InventoryTransaction.transaction_type == "in",
                 or_(
                     InventoryTransaction.notes.ilike("%initial stock%"),
                     InventoryTransaction.notes.ilike("%opening balance%")
                 )
             )
        elif type == "purchase":
             # Purchase means 'in' BUT NOT initial stock
             query = query.filter(
                 InventoryTransaction.transaction_type == "in",
                 ~or_(
                     InventoryTransaction.notes.ilike("%initial stock%"),
                     InventoryTransaction.notes.ilike("%opening balance%")
                 )
             )
        elif type == "usage": # Kitchen usage
             query = query.filter(InventoryTransaction.transaction_type == "out")
             # Optionally verify it's not waste? Frontend does this check.
             # "usage" usually means NOT waste.
             query = query.filter(
                 ~or_(
                     InventoryTransaction.notes.ilike("%waste%"),
                     InventoryTransaction.notes.ilike("%spoilage%")
                 )
             )
        elif type == "waste":
             query = query.filter(
                 InventoryTransaction.transaction_type == "out",
                 or_(
                     InventoryTransaction.notes.ilike("%waste%"),
                     InventoryTransaction.notes.ilike("%spoilage%")
                 )
             )
        else:
             # Standard types: transfer_in, transfer_out, adjustment
             query = query.filter(InventoryTransaction.transaction_type == type)

    # Filter by Date
    if start_date:
        try:
            # Handle potential ISO format differences
            s_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(InventoryTransaction.created_at >= s_date)
        except:
             pass # Ignore invalid date
             
    if end_date:
        try:
             e_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
             # Set to end of day? Usually frontend sends 23:59:59
             query = query.filter(InventoryTransaction.created_at <= e_date)
        except:
             pass

    # Filter by Category
    if category and category != "all":
        query = query.join(InventoryItem.category).filter(InventoryCategory.name == category)

    # Search
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                InventoryItem.name.ilike(search_term),
                InventoryTransaction.notes.ilike(search_term),
                InventoryTransaction.reference_number.ilike(search_term)
            )
        )

    transactions = query.order_by(InventoryTransaction.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for trans in transactions:
        # Get destination location if this is a stock issue
        destination_location_name = None
        if trans.reference_number and trans.reference_number.startswith("ISS-"):
            # Try to find the stock issue and get destination location
            issue = db.query(StockIssue).filter(StockIssue.issue_number == trans.reference_number).first()
            if issue and issue.destination_location_id:
                dest_loc = inventory_crud.get_location_by_id(db, issue.destination_location_id)
                if dest_loc:
                    destination_location_name = f"{dest_loc.building} - {dest_loc.room_area}" if (dest_loc.building or dest_loc.room_area) else dest_loc.name or f"Location {dest_loc.id}"
        
        # Relationships already loaded, no extra queries
        result.append({
            **trans.__dict__,
            "item_name": trans.item.name if trans.item else None,
            "created_by_name": trans.user.name if trans.user else None,
            "destination_location_name": destination_location_name
        })
    return result


# Stock Requisition Endpoints
@router.post("/requisitions", response_model=StockRequisitionOut)
def create_requisition(
    requisition: StockRequisitionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        requisition_data = requisition.model_dump()
        created = inventory_crud.create_stock_requisition(db, requisition_data, created_by=current_user.id)
        
        # Load relationships for response
        requester = db.query(User).filter(User.id == created.requested_by).first()
        details = []
        for detail in created.details:
            item = inventory_crud.get_item_by_id(db, detail.item_id)
            details.append({
                **detail.__dict__,
                "item_name": item.name if item else None
            })
        
        return {
            **created.__dict__,
            "requested_by_name": requester.name if requester else None,
            "details": details
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating requisition: {str(e)}")


@router.get("/requisitions", response_model=List[StockRequisitionOut])
def get_requisitions(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Optimized with eager loading - no N+1 queries"""
    requisitions = inventory_crud.get_all_requisitions(db, skip=skip, limit=limit, status=status)
    result = []
    for req in requisitions:
        # Items already loaded via eager loading
        requester = db.query(User).filter(User.id == req.requested_by).first()
        approver = db.query(User).filter(User.id == req.approved_by).first() if req.approved_by else None
        details = []
        for detail in req.details:
            item = detail.item  # Already loaded
            details.append({
                **detail.__dict__,
                "item_name": item.name if item else None,
                "current_stock": item.current_stock if item else None
            })
        result.append({
            **req.__dict__,
            "requested_by_name": requester.name if requester else None,
            "approved_by_name": approver.name if approver else None,
            "details": details
        })
    return result


@router.patch("/requisitions/{requisition_id}/status")
def update_requisition_status(
    requisition_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    requisition = inventory_crud.update_requisition_status(db, requisition_id, status, approved_by=current_user.id)
    if not requisition:
        raise HTTPException(status_code=404, detail="Requisition not found")
    return {"message": "Requisition status updated successfully", "status": requisition.status}


@router.put("/requisitions/{requisition_id}/approve-quantities")
def approve_requisition_quantities(
    requisition_id: int,
    approved_quantities: dict,  # {detail_id: approved_quantity}
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update approved quantities for requisition details"""
    from app.models.inventory import StockRequisitionDetail
    for detail_id, approved_qty in approved_quantities.items():
        detail = db.query(StockRequisitionDetail).filter(StockRequisitionDetail.id == detail_id).first()
        if detail and detail.requisition_id == requisition_id:
            detail.approved_quantity = approved_qty
    db.commit()
    return {"message": "Approved quantities updated successfully"}


@router.get("/stocks", response_model=List[dict])
def get_all_stocks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.inventory import LocationStock
    stocks = db.query(LocationStock).filter(LocationStock.quantity > 0).all()
    result = []
    for s in stocks:
        result.append({
            "location_id": s.location_id,
            "item_id": s.item_id,
            "quantity": float(s.quantity)
        })
    return result


# Stock Issue Endpoints
@router.post("/issues", response_model=StockIssueOut)
def create_issue(
    issue: StockIssueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        issue_data = issue.model_dump()
        created = inventory_crud.create_stock_issue(db, issue_data, issued_by=current_user.id)
        
        # Optimized: Batch load to avoid N+1 queries
        issuer = db.query(User).filter(User.id == created.issued_by).first()
        source_loc = inventory_crud.get_location_by_id(db, created.source_location_id) if created.source_location_id else None
        dest_loc = inventory_crud.get_location_by_id(db, created.destination_location_id) if created.destination_location_id else None
        
        # Batch load items
        detail_item_ids = [d.item_id for d in created.details if d.item_id]
        items_map = {}
        if detail_item_ids:
            from app.models.inventory import InventoryItem
            items = db.query(InventoryItem).filter(InventoryItem.id.in_(detail_item_ids)).all()
            items_map = {item.id: item for item in items}
        
        details = []
        for detail in created.details:
            item = items_map.get(detail.item_id) if detail.item_id else None
            details.append({
                **detail.__dict__,
                "item_name": item.name if item else None
            })
        
        return {
            **created.__dict__,
            "issued_by_name": issuer.name if issuer else None,
            "source_location_name": f"{source_loc.building} - {source_loc.room_area}" if source_loc else None,
            "destination_location_name": f"{dest_loc.building} - {dest_loc.room_area}" if dest_loc else None,
            "details": details
        }
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # If it's already an HTTPException (like our 400 validation error), re-raise it
        if isinstance(e, HTTPException):
            raise e
            
        import traceback
        traceback.print_exc()
        # Log to file for debugging
        try:
            with open("api_stock_issue_error.log", "a") as f:
                f.write(f"\n{'='*80}\n{datetime.now()}\nError: {str(e)}\n{traceback.format_exc()}{'='*80}\n")
        except:
            pass
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating issue: {str(e)}")


@router.get("/issues", response_model=List[StockIssueOut])
def get_issues(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Optimized with eager loading - no N+1 queries"""
    issues = inventory_crud.get_all_issues(db, skip=skip, limit=limit)
    result = []
    for issue in issues:
        # Locations and items already loaded via eager loading
        issuer = db.query(User).filter(User.id == issue.issued_by).first()
        source_loc = issue.source_location  # Already loaded
        dest_loc = issue.destination_location  # Already loaded
        details = []
        for detail in issue.details:
            item = detail.item  # Already loaded
            # Parse payment status from notes
            is_paid = detail.notes and "PAID" in detail.notes.upper() if detail.notes else False
            details.append({
                **detail.__dict__,
                "item_name": item.name if item else None,
                "is_paid": is_paid
            })
        result.append({
            **issue.__dict__,
            "issued_by_name": issuer.name if issuer else None,
            "source_location_name": f"{source_loc.building} - {source_loc.room_area}" if source_loc else None,
            "destination_location_name": f"{dest_loc.building} - {dest_loc.room_area}" if dest_loc else None,
            "details": details
        })
    return result


@router.patch("/issues/{issue_id}/details/{detail_id}")
def update_issue_detail(
    issue_id: int,
    detail_id: int,
    is_payable: Optional[bool] = None,
    is_paid: Optional[bool] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update issue detail payable/paid status"""
    from app.models.inventory import StockIssueDetail
    
    detail = db.query(StockIssueDetail).filter(
        StockIssueDetail.id == detail_id,
        StockIssueDetail.issue_id == issue_id
    ).first()
    
    if not detail:
        raise HTTPException(status_code=404, detail="Issue detail not found")
    
    # Update notes to reflect payable and paid status
    current_notes = detail.notes or ""
    
    # Parse existing notes to preserve other information
    note_parts = []
    if notes:
        note_parts.append(notes)
    elif current_notes and "PAID" not in current_notes.upper() and "UNPAID" not in current_notes.upper():
        note_parts.append(current_notes)
    
    # Update payable status
    if is_payable is not None:
        if is_payable:
            if "Payable item" not in current_notes:
                note_parts.append("Payable item")
            if "Complimentary item" in current_notes:
                current_notes = current_notes.replace("Complimentary item", "").strip()
        else:
            if "Complimentary item" not in current_notes:
                note_parts.append("Complimentary item")
            if "Payable item" in current_notes:
                current_notes = current_notes.replace("Payable item", "").strip()
    
    # Update paid status
    if is_paid is not None:
        # Remove existing PAID/UNPAID markers
        current_notes = current_notes.replace(" - PAID", "").replace(" - UNPAID", "").replace("PAID", "").replace("UNPAID", "").strip()
        if is_paid:
            note_parts.append("PAID")
        else:
            note_parts.append("UNPAID")
    
    # Combine notes
    detail.notes = " - ".join([p for p in note_parts if p.strip()])
    
    db.commit()
    db.refresh(detail)
    
    return {
        "id": detail.id,
        "item_id": detail.item_id,
        "notes": detail.notes,
        "is_payable": "Payable item" in detail.notes if detail.notes else False,
        "is_paid": "PAID" in detail.notes.upper() if detail.notes else False
    }


# Waste Log Endpoints
@router.post("/waste-logs", response_model=WasteLogOut)
def create_waste_log(
    item_id: Optional[str] = Form(None),
    food_item_id: Optional[str] = Form(None),
    is_food_item: Optional[str] = Form(None),
    location_id: Optional[str] = Form(None),
    batch_number: Optional[str] = Form(None),
    expiry_date: Optional[str] = Form(None),
    quantity: str = Form(...),
    unit: str = Form(...),
    reason_code: str = Form(...),
    action_taken: Optional[str] = Form(None),
    waste_date: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        from datetime import datetime as dt
        
        # Manual conversion
        parsed_item_id = int(item_id) if item_id and item_id.strip() else None
        parsed_food_item_id = int(food_item_id) if food_item_id and food_item_id.strip() else None
        parsed_location_id = int(location_id) if location_id and location_id.strip() else None
        parsed_quantity = float(quantity)
        parsed_is_food = is_food_item in ["true", "True", "1", "on"] if is_food_item else False

        waste_data = {
            "item_id": parsed_item_id,
            "food_item_id": parsed_food_item_id,
            "is_food_item": parsed_is_food,
            "location_id": parsed_location_id,
            "batch_number": batch_number,
            "expiry_date": dt.strptime(expiry_date, "%Y-%m-%d").date() if expiry_date else None,
            "quantity": parsed_quantity,
            "unit": unit,
            "reason_code": reason_code,
            "action_taken": action_taken if action_taken else None,
            "waste_date": dt.strptime(waste_date, "%Y-%m-%d") if waste_date else dt.now(),
            "notes": notes,
        }
        
        # Handle photo upload
        if photo and photo.filename:
            WASTE_UPLOAD_DIR = "uploads/waste_logs"
            os.makedirs(WASTE_UPLOAD_DIR, exist_ok=True)
            filename = f"waste_{uuid.uuid4().hex}_{photo.filename}"
            file_path = os.path.join(WASTE_UPLOAD_DIR, filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(photo.file, buffer)
            waste_data["photo_path"] = f"uploads/waste_logs/{filename}".replace("\\", "/")
        
        created = inventory_crud.create_waste_log(db, waste_data, reported_by=current_user.id)
        
        # Load relationships for response
        reporter = db.query(User).filter(User.id == created.reported_by).first()
        item = inventory_crud.get_item_by_id(db, created.item_id) if created.item_id else None
        food_item = None
        if created.food_item_id:
            from app.models.food_item import FoodItem
            food_item = db.query(FoodItem).filter(FoodItem.id == created.food_item_id).first()
            
        location = inventory_crud.get_location_by_id(db, created.location_id) if created.location_id else None
        
        return {
            **created.__dict__,
            "reported_by_name": reporter.name if reporter else None,
            "item_name": item.name if item else None,
            "food_item_name": food_item.name if food_item else None,
            "location_name": f"{location.building} - {location.room_area}" if location else None
        }
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating waste log: {str(e)}")


@router.get("/waste-logs", response_model=List[WasteLogOut])
def get_waste_logs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Optimized with eager loading"""
    from app.models.inventory import WasteLog
    from sqlalchemy.orm import joinedload
    waste_logs = db.query(WasteLog).options(
        joinedload(WasteLog.item),
        joinedload(WasteLog.location)
    ).order_by(WasteLog.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for log in waste_logs:
        reporter = db.query(User).filter(User.id == log.reported_by).first()
        item_name = log.item.name if log.item else None
        food_item_name = None
        
        if log.is_food_item and not item_name:
             from app.models.food_item import FoodItem
             food_item = db.query(FoodItem).filter(FoodItem.id == log.food_item_id).first()
             if food_item:
                 food_item_name = food_item.name
                 
        location = log.location  # Already loaded
        result.append({
            **log.__dict__,
            "reported_by_name": reporter.name if reporter else None,
            "item_name": item_name,
            "food_item_name": food_item_name,
            "location_name": f"{location.building} - {location.room_area}" if location else None
        })
    return result


# Location Endpoints
@router.post("/locations", response_model=LocationOut)
def create_location(
    location: LocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    location_data = location.model_dump()
    created = inventory_crud.create_location(db, location_data)
    return created


@router.get("/locations", response_model=List[dict])
def get_locations(
    skip: int = 0,
    limit: int = 10000,  # Increased limit to show all rooms
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Auto-sync rooms to locations
    from app.models.room import Room
    from app.models.inventory import Location
    from sqlalchemy import or_
    
    # Optimized: Only sync if there are unsynced rooms (performance optimization)
    unsynced_count = db.query(Room).filter(Room.inventory_location_id == None).count()
    
    if unsynced_count > 0:
        # Auto-sync rooms to locations (batch operation for better performance)
        try:
            rooms_to_sync = db.query(Room).filter(Room.inventory_location_id == None).all()
            
            for room in rooms_to_sync:
                try:
                    # Check if location already exists for this room
                    existing_location = db.query(Location).filter(
                        or_(
                            Location.name == f"Room {room.number}",
                            Location.room_area == f"Room {room.number}"
                        ),
                        Location.location_type == "GUEST_ROOM"
                    ).first()
                    
                    if not existing_location:
                        # Create new location for room
                        location_data = {
                            "name": f"Room {room.number}",
                            "building": "Main Building",
                            "floor": None,
                            "room_area": f"Room {room.number}",
                            "location_type": "GUEST_ROOM",
                            "is_inventory_point": False,
                            "description": f"Guest room {room.number} - {room.type or 'Standard'}",
                            "is_active": (room.status != "Deleted" if room.status else True)
                        }
                        location = inventory_crud.create_location(db, location_data)
                        room.inventory_location_id = location.id
                        db.commit()
                    else:
                        # Link room to existing location
                        room.inventory_location_id = existing_location.id
                        db.commit()
                except Exception as e:
                    # Skip this room and continue
                    db.rollback()
                    print(f"Warning: Could not sync room {room.number}: {str(e)}")
                    continue
        except Exception as e:
            # If sync fails completely, just log and continue
            print(f"Warning: Room sync skipped: {str(e)}")
            try:
                db.rollback()
            except:
                pass
    
    # Now fetch all locations (optimized with eager loading)
    from sqlalchemy.orm import joinedload
    from sqlalchemy import func
    from app.models.inventory import LocationStock, InventoryItem, AssetRegistry
    
    locations = db.query(Location).options(
        joinedload(Location.parent_location)
    ).filter(Location.is_active == True).offset(skip).limit(limit).all()
    
    # Bulk Calculate Stats (Optimization)
    
    # 1. Consumables (LocationStock)
    stock_stats = db.query(
        LocationStock.location_id,
        func.count(LocationStock.id),
        func.sum(LocationStock.quantity * InventoryItem.unit_price)
    ).join(InventoryItem, LocationStock.item_id == InventoryItem.id)\
     .filter(LocationStock.quantity > 0)\
     .group_by(LocationStock.location_id).all()
     
    stock_map = {loc_id: {"count": c, "value": v or 0} for loc_id, c, v in stock_stats}
    
    # 2. Fixed Assets (AssetRegistry) - Include these in value/count
    asset_stats = db.query(
        AssetRegistry.current_location_id,
        func.count(AssetRegistry.id),
        func.sum(InventoryItem.unit_price)
    ).join(InventoryItem, AssetRegistry.item_id == InventoryItem.id)\
     .filter(AssetRegistry.status == 'active')\
     .group_by(AssetRegistry.current_location_id).all()
     
    asset_map = {loc_id: {"count": c, "value": v or 0} for loc_id, c, v in asset_stats}
    
    result = []
    for loc in locations:
        parent = loc.parent_location
        
        # Merge stats
        s_data = stock_map.get(loc.id, {"count": 0, "value": 0})
        a_data = asset_map.get(loc.id, {"count": 0, "value": 0})
        
        total_items = (s_data["count"] or 0) + (a_data["count"] or 0)
        total_value = float(s_data["value"] or 0) + float(a_data["value"] or 0)
        
        # Convert model instance to dict safely
        loc_dict = {c.name: getattr(loc, c.name) for c in loc.__table__.columns}
        
        result.append({
            **loc_dict,
            "parent_location_name": f"{parent.building} - {parent.room_area}" if parent else None,
            "total_items": total_items,
            "total_value": total_value,
            "asset_count": a_data["count"],
            "consumable_count": s_data["count"]
        })
    return result


@router.get("/locations/{location_id}/items")
def get_location_items(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all inventory items and their stock levels for a specific location"""
    from app.models.inventory import InventoryItem, AssetMapping, AssetRegistry, StockIssueDetail, StockIssue, LocationStock, WasteLog
    from sqlalchemy import func
    from sqlalchemy.orm import joinedload
    from datetime import datetime, timedelta
    
    location = inventory_crud.get_location_by_id(db, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # 1. Get items from LocationStock (Primary Source for bulk items)
    # 1. Get items from LocationStock (Primary Source for bulk items)
    location_stocks = db.query(LocationStock).filter(
        LocationStock.location_id == location_id,
        LocationStock.quantity != 0
    ).all()
    
    # 2. Get items assigned to this location via asset mappings
    asset_mappings = db.query(AssetMapping).filter(
        AssetMapping.location_id == location_id,
        AssetMapping.is_active == True
    ).all()
    
    # 3. Get items from asset registry (Only active/in_stock assets should count as current location stock)
    asset_registry = db.query(AssetRegistry).filter(
        AssetRegistry.current_location_id == location_id,
        AssetRegistry.status.in_(["active", "in_stock", "In Stock"])
    ).all()
    
    # Combine all items
    items_dict = {}
    
    # Pre-calculate mapped quantities to prioritize stock attribution
    mapped_counts = {}
    for m in asset_mappings:
        mapped_counts[m.item_id] = mapped_counts.get(m.item_id, 0) + (m.quantity or 1)
    
    # Add items from LocationStock
    # Add items from LocationStock
    for stock in location_stocks:
        item = stock.item
        if item:
            category = inventory_crud.get_category_by_id(db, item.category_id)
            
            # Fetch all issue details ordered by date DESC
            issue_details = db.query(StockIssueDetail).join(StockIssue).filter(
                StockIssue.destination_location_id == location_id,
                StockIssueDetail.item_id == item.id
            ).order_by(StockIssue.issue_date.desc()).all()
            
            # Split issues into Rented vs Standard (Exclude damaged items from currently active pool)
            available_rented_issues = [d for d in issue_details if ((d.rental_price and d.rental_price > 0) or d.is_payable) and not (d.is_damaged == True)]
            
            # Determine split quantities based on current stock
            total_rented_need = sum(float(d.issued_quantity) for d in available_rented_issues)
            current_stock_qty = float(stock.quantity)
            
            # LOGIC: First reserve stock for Mapped Assets (Fixed), then assign to Rentals, then the rest is standard
            mapped_need = float(mapped_counts.get(item.id, 0))
            
            # 1. Base Standard = min(stock, mapped_need)
            base_standard = min(current_stock_qty, mapped_need)
            remaining_after_mapped = current_stock_qty - base_standard
            
            # 2. Rented = min(remaining, total_rented_need)
            rented_stock_qty = min(remaining_after_mapped, total_rented_need)
            
            # 3. Final Standard = base_standard + whatever is left
            standard_stock_qty = base_standard + (remaining_after_mapped - rented_stock_qty)
            
            # Helper to process a batch and add to items_dict
            def process_batch(qty, issues, key_suffix, is_rent_split):
                # Don't show 0 qty rows unless it's the standard row (to show item exists)
                if qty == 0 and (is_rent_split or (current_stock_qty > 0)): 
                    return

                complimentary_qty = 0.0
                payable_qty = 0.0
                remaining = qty
                last_issue_price = 0.0
                
                # Attribute stock to issues (LIFO based on query order)
                for detail in issues:
                    if remaining <= 0: break
                    issued = float(detail.issued_quantity)
                    attributed = min(remaining, issued)
                    
                    if detail.is_payable:
                        payable_qty += attributed
                        p = detail.rental_price if detail.rental_price and detail.rental_price > 0 else detail.unit_price
                        if p and p > 0 and last_issue_price == 0:
                            last_issue_price = float(p)
                    else:
                        complimentary_qty += attributed
                    remaining -= attributed
                
                # Pricing
                selling_price = last_issue_price if last_issue_price > 0 else (item.selling_price if item.selling_price and item.selling_price > 0 else item.unit_price)
                cost_price = item.unit_price or 0
                stock_value = qty * cost_price
                
                key = f"item_{item.id}{key_suffix}"
                
                # Type determination
                is_asset = ((category and category.is_asset_fixed) or item.is_asset_fixed or item.track_laundry_cycle or (not item.is_sellable_to_guest and not item.is_perishable))
                
                items_dict[key] = {
                    "item_id": item.id,
                    "item_name": item.name,
                    "item_code": item.item_code,
                    "category_name": category.name if category else None,
                    "unit": item.unit,
                    "current_stock": qty,
                    "location_stock": qty,
                    "complimentary_qty": complimentary_qty,
                    "payable_qty": payable_qty,
                    "min_stock_level": item.min_stock_level,
                    "unit_price": cost_price,
                    "cost_price": cost_price,
                    "selling_price": selling_price,
                    "total_value": stock_value,
                    "source": "Stock" + (" (Rented)" if is_rent_split else ""),
                    "last_updated": stock.last_updated,
                    "type": "asset" if is_asset else "consumable",
                    
                    # Add explicit rental flags
                    "is_rentable": is_rent_split, 
                    "is_asset_fixed": item.is_asset_fixed 
                }

            # 1. Process Rented
            if rented_stock_qty != 0:
                process_batch(rented_stock_qty, available_rented_issues, "_rented", True)
                
            # 2. Process Standard
            if standard_stock_qty != 0 or (rented_stock_qty == 0):
                # Use all issues for standard pool pricing fallback
                process_batch(standard_stock_qty, issue_details, "", False)



    # Add items from asset mappings - These are permanently assigned assets
    # MERGE with LocationStock items if they exist to prevent duplicates
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
                    "source": items_dict[stock_key]["source"] + ", Asset Mapping" # Update source
                })
                # We do NOT add a new asset_mapped_ entry to avoid duplicates
            else:
                # Add as new entry if not in LocationStock
                # Use standard key format to ensure consistency
                key = f"asset_mapped_{item.id}"
                
                category = inventory_crud.get_category_by_id(db, item.category_id)
                items_dict[key] = {
                    "item_id": item.id,
                    "item_name": item.name,
                    "item_code": item.item_code,
                    "category_name": category.name if category else None,
                    "unit": item.unit,
                    "current_stock": mapping.quantity or 1, 
                    "location_stock": mapping.quantity or 1,
                    "min_stock_level": item.min_stock_level,
                    "unit_price": item.unit_price,
                    "total_value": (item.unit_price or 0) * (mapping.quantity or 1),
                    "source": "Asset Mapping",
                    "serial_number": mapping.serial_number,
                    "assigned_date": mapping.assigned_date,
                    "type": "asset",
                    "is_fixed_asset": True,
                    "is_rentable": False
                }

    # Add items from asset registry
    for asset in asset_registry:
        item = asset.item
        if item:
            key = f"registry_{asset.id}" # Unique per asset instance
            category = inventory_crud.get_category_by_id(db, item.category_id)
            items_dict[key] = {
                "item_id": item.id,
                "item_name": item.name,
                "item_code": item.item_code,
                "category_name": category.name if category else None,
                "unit": item.unit,
                "current_stock": 1,
                "location_stock": 1, # Alias for frontend
                "min_stock_level": item.min_stock_level,
                "unit_price": item.unit_price,
                "total_value": item.unit_price or 0,
                "source": "Asset Registry",
                "serial_number": asset.serial_number,
                "asset_tag": asset.asset_tag_id,
                "status": asset.status,
                "type": "asset"
            }
    
    # 4. Get History (Stock Issues & Waste Logs)
    history = []
    
    # Stock Issues (Inbound to location)
    stock_issues_in = db.query(StockIssue).options(
        joinedload(StockIssue.details).joinedload(StockIssueDetail.item),
        joinedload(StockIssue.issuer)
    ).filter(
        StockIssue.destination_location_id == location_id
    ).order_by(StockIssue.issue_date.desc()).limit(50).all()
    
    for issue in stock_issues_in:
        for detail in issue.details:
            if detail.item:
                history.append({
                    "date": issue.issue_date,
                    "type": "Stock Received",
                    "item_name": detail.item.name,
                    "quantity": detail.issued_quantity,
                    "unit": detail.unit,
                    "reference": issue.issue_number,
                    "user": issue.issuer.name if issue.issuer else "Unknown",
                    "notes": detail.notes or issue.notes,
                    "color": "green"
                })

    # Stock Issues (Outbound from location - Transfers)
    stock_issues_out = db.query(StockIssue).options(
        joinedload(StockIssue.details).joinedload(StockIssueDetail.item),
        joinedload(StockIssue.issuer),
        joinedload(StockIssue.destination_location)
    ).filter(
        StockIssue.source_location_id == location_id
    ).order_by(StockIssue.issue_date.desc()).limit(50).all()

    for issue in stock_issues_out:
        dest_name = issue.destination_location.name if issue.destination_location else "Unknown"
        for detail in issue.details:
            if detail.item:
                history.append({
                    "date": issue.issue_date,
                    "type": "Transfer Out", # Or "Stock Issued"
                    "item_name": detail.item.name,
                    "quantity": detail.issued_quantity,
                    "unit": detail.unit,
                    "reference": issue.issue_number,
                    "user": issue.issuer.name if issue.issuer else "Unknown",
                    "notes": f"To {dest_name} - {detail.notes or issue.notes}",
                    "color": "orange" # Distinct color for transfers
                })

    # Waste Logs (Outbound/Loss from location)
    waste_logs = db.query(WasteLog).options(
        joinedload(WasteLog.item),
        joinedload(WasteLog.food_item),
        joinedload(WasteLog.reporter)
    ).filter(
        WasteLog.location_id == location_id
    ).order_by(WasteLog.waste_date.desc()).limit(50).all()
    
    for log in waste_logs:
        item_name = log.item.name if log.item else (log.food_item.name if log.food_item else "Unknown Item")
        history.append({
            "date": log.waste_date,
            "type": f"Waste ({log.reason_code})",
            "item_name": item_name,
            "quantity": log.quantity,
            "unit": log.unit,
            "reference": log.log_number,
            "user": log.reporter.name if log.reporter else "Unknown",
            "notes": log.notes,
            "color": "red"
        })

    # 5. Get Purchase History (Directly Received at Location)
    from app.models.inventory import PurchaseMaster, PurchaseDetail
    
    purchases = db.query(PurchaseDetail).join(PurchaseMaster).options(
        joinedload(PurchaseDetail.item),
        joinedload(PurchaseDetail.purchase_master).joinedload(PurchaseMaster.user)
    ).filter(
        PurchaseMaster.destination_location_id == location_id,
        PurchaseMaster.status == "received"
    ).order_by(PurchaseMaster.updated_at.desc()).limit(50).all()
    
    for detail in purchases:
        purchase = detail.purchase_master
        if detail.item:
            history.append({
                "date": purchase.updated_at, # Using updated_at as receive date proxy
                "type": "Purchase Received",
                "item_name": detail.item.name,
                "quantity": detail.quantity,
                "unit": detail.unit,
                "reference": purchase.purchase_number,
                "user": purchase.user.name if purchase.user else "System",
                "notes": f"Vendor: {purchase.vendor.name if purchase.vendor else 'Unknown'}",
                "color": "green"  # Green for incoming stock (positive quantity)
            })
    
    # 6. Get Adjustment History (InventoryTransactions)
    # This covers manual adjustments and auto-corrections from checkout
    from app.models.inventory import InventoryTransaction
    
    # Adjustments affecting this location specifically
    # Note: InventoryTransaction usually tracks global stock or is loosely coupled. 
    # But if we used specific references like "ADJ-CHK-...-LOC-{id}", we could filter.
    # However, my checkout fix used: reference_number=f"ADJ-CHK-{checkout_request.id}"
    # and notes=f"... Deducted from Source ID {adjust_source_id}."
    # This makes it hard to filter by location_id purely from DB query without a JOIN or structured ref.
    # But we can try to find transactions referencing this location in notes or reference? 
    # Better: If we want to show it in History, we should rely on WasteLog or StockIssue.
    # Since Step 3c created an InventoryTransaction but not a WasteLog/StockIssue for the source deduction, 
    # it is invisible here. 
    # TO FIX VISIBILITY: We will fetch InventoryTransactions that have this item and seem to be adjustments,
    # and filter in python if they mention this location.
    
    # 6. Get Adjustment History (InventoryTransactions)
    # Filter for items that are present in this location view
    location_item_ids = []
    for k in items_dict.keys():
        if k.startswith("item_"):
            try:
                location_item_ids.append(int(k.split('_')[1]))
            except: pass
        elif k.startswith("registry_"):
            # Getting item id from registry key might be harder unless we stored it
            if "item_id" in items_dict[k]:
                 location_item_ids.append(items_dict[k]["item_id"])

    # Remove duplicates
    location_item_ids = list(set(location_item_ids))
    
    adjustments = []
    if location_item_ids:
        adjustments = db.query(InventoryTransaction).options(
            joinedload(InventoryTransaction.user)
        ).filter(
            InventoryTransaction.item_id.in_(location_item_ids),
            InventoryTransaction.created_at >= (datetime.now() - timedelta(days=30))
        ).all()

    # Iterate and filter manually for this location context
    for adj in adjustments:
        # Check if this transaction is relevant to this location
        # Our checkout fix used: reference_number=f"ADJ-CHK-{checkout_request.id}"
        # and notes=f"... Deducted from Source ID {adjust_source_id}."
        
        is_relevant = False
        if str(location.id) in (adj.notes or "") and "Source ID" in (adj.notes or ""):
             is_relevant = True
        elif adj.reference_number and f"LOC-{location.id}" in adj.reference_number:
             is_relevant = True
             
        if is_relevant:
            item_name = "Unknown Item"
            if adj.item: # If eager loaded or available
                item_name = adj.item.name
            else:
                 # Fetch item name if not loaded
                 from app.models.inventory import InventoryItem
                 tmp_item = db.query(InventoryItem).filter(InventoryItem.id == adj.item_id).first()
                 if tmp_item: item_name = tmp_item.name

            history.append({
                "date": adj.created_at,
                "type": "Stock Adjustment",
                "item_name": item_name,
                "quantity": -adj.quantity if adj.transaction_type == "out" else adj.quantity, # Negative for deduction
                "unit": "units", # Fallback
                "reference": adj.reference_number,
                "user": adj.user.name if adj.user else "System",
                "notes": adj.notes,
                "color": "red" if adj.transaction_type == "out" else "orange"
            })
    
    # Sort combined history by date desc
    history.sort(key=lambda x: x["date"], reverse=True)

    items_list = list(items_dict.values())
    total_items = len(items_list) # Use item count/rows instead of quantity sum
    total_value = sum(item["total_value"] for item in items_list)
    
    return {
        "location": {
            "id": location.id,
            "name": location.name,
            "building": location.building,
            "floor": location.floor,
            "room_area": location.room_area,
            "location_type": location.location_type
        },
        "total_items": total_items, # This is the sum of CURRENT LocationStock
        "total_stock_value": total_value,
        "items": items_list,
        "history": history
    }



@router.get("/stock-by-location")
def get_stock_by_location(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get inventory stock summary grouped by location - OPTIMIZED"""
    from app.models.inventory import Location, AssetMapping, AssetRegistry, LocationStock, InventoryItem, InventoryCategory
    from sqlalchemy import func
    from sqlalchemy.orm import joinedload
    
    try:
        # 1. Fetch all locations at once
        locations = inventory_crud.get_all_locations(db, skip=0, limit=1000)
        location_ids = [loc.id for loc in locations]
        location_map = {loc.id: loc for loc in locations}
        
        # 2. Bulk fetch all LocationStock with eager loading
        all_location_stocks = db.query(LocationStock).options(
            joinedload(LocationStock.item),
            joinedload(LocationStock.location)
        ).filter(
            LocationStock.location_id.in_(location_ids)
        ).all()
        
        # 3. Bulk fetch all AssetMappings
        all_asset_mappings = db.query(AssetMapping).options(
            joinedload(AssetMapping.item)
        ).filter(
            AssetMapping.location_id.in_(location_ids),
            AssetMapping.is_active == True
        ).all()
        
        # 4. Bulk fetch all AssetRegistry
        all_registry_items = db.query(AssetRegistry).options(
            joinedload(AssetRegistry.item)
        ).filter(
            AssetRegistry.current_location_id.in_(location_ids)
        ).all()
        
        # 5. Bulk fetch all categories for items
        item_ids = set()
        for stock in all_location_stocks:
            if stock.item:
                item_ids.add(stock.item_id)
        for mapping in all_asset_mappings:
            item_ids.add(mapping.item_id)
        for reg in all_registry_items:
            item_ids.add(reg.item_id)
        
        categories_map = {}
        if item_ids:
            items_with_cats = db.query(InventoryItem).options(
                joinedload(InventoryItem.category)
            ).filter(InventoryItem.id.in_(item_ids)).all()
            for item in items_with_cats:
                if item.category:
                    categories_map[item.id] = item.category
            
            # Map item objects for calculation
            items_obj_map = {item.id: item for item in items_with_cats}
        
        # 5. Organize data by location
        location_data = {}
        for loc_id in location_ids:
            location_data[loc_id] = {
                'items_map': {},
                'seen_items': set(),
                'total_items': 0,
                'asset_count': 0,
                'consumable_count': 0,
                'total_stock_value': 0.0
            }
        
        # 6. Process LocationStock (PRIMARY source)
        for stock in all_location_stocks:
            loc_id = stock.location_id
            if loc_id in location_data:
                # Only track if quantity is non-zero (exclude empty stock from variety count, include negative)
                if stock.quantity != 0:
                    location_data[loc_id]['seen_items'].add(stock.item_id)
                    location_data[loc_id]['items_map'][stock.item_id] = stock.quantity
        
        # 7. Process AssetMappings (only if not in LocationStock)
        for mapping in all_asset_mappings:
            loc_id = mapping.location_id
            if loc_id in location_data and mapping.item_id not in location_data[loc_id]['seen_items']:
                location_data[loc_id]['items_map'][mapping.item_id] = mapping.quantity
                location_data[loc_id]['seen_items'].add(mapping.item_id)
        
        # 8. Process AssetRegistry (only if not seen)
        registry_counts = {}
        for reg in all_registry_items:
            key = (reg.current_location_id, reg.item_id)
            registry_counts[key] = registry_counts.get(key, 0) + 1
        
        for (loc_id, item_id), count in registry_counts.items():
            if loc_id in location_data and item_id not in location_data[loc_id]['seen_items']:
                location_data[loc_id]['items_map'][item_id] = count
        
        # 9. Calculate totals (items and categories are already loaded)
        # 9. Calculate totals (Iterate aggregated items_map to include Stocks, Mappings, and Registry)
        # This fixes missing values for items that are only mapped/registered but not in LocationStock
        for loc_id, data in location_data.items():
            for item_id, qty in data['items_map'].items():
                item = items_obj_map.get(item_id)
                if item:
                    # Value
                    val = qty * (item.unit_price or 0)
                    data['total_stock_value'] += val

                    # Counts (Asset vs Consumable)
                    category = categories_map.get(item_id)
                    is_asset = item.is_asset_fixed or \
                              (category and category.is_asset_fixed) or \
                              item.track_laundry_cycle
                    
                    if is_asset:
                        data['asset_count'] += qty
                    else:
                        data['consumable_count'] += qty
        
        # 10. Build result
        result = []
        for location in locations:
            data = location_data[location.id]
            result.append({
                **location.__dict__,
                "asset_count": data['asset_count'],
                "consumable_items_count": data['consumable_count'],
                "total_stock_value": data['total_stock_value'],
                "total_items": len(data['items_map']) # Use variety count instead of quantity sum
            })
        
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching stock by location: {str(e)}")


@router.post("/locations/sync-rooms")
def sync_rooms_to_locations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Synchronize existing rooms from rooms table to locations table for inventory"""
    from app.models.room import Room
    from app.models.inventory import Location
    from app.curd import inventory as inventory_crud
    
    try:
        rooms = db.query(Room).all()
        synced_count = 0
        created_count = 0
        linked_count = 0
        
        for room in rooms:
            # Check if location already exists for this room
            from sqlalchemy import or_
            existing_location = db.query(Location).filter(
                or_(
                    Location.name == f"Room {room.number}",
                    Location.room_area == f"Room {room.number}"
                ),
                Location.location_type == "GUEST_ROOM"
            ).first()
            
            if existing_location:
                # Link room to existing location
                if not room.inventory_location_id:
                    room.inventory_location_id = existing_location.id
                    linked_count += 1
                synced_count += 1
            else:
                # Create new location for room using CRUD function
                location_data = {
                    "name": f"Room {room.number}",
                    "building": "Main Building",  # Default, can be updated later
                    "floor": None,  # Can be extracted from room number if needed
                    "room_area": f"Room {room.number}",
                    "location_type": "GUEST_ROOM",
                    "is_inventory_point": False,  # Rooms are not inventory points
                    "description": f"Guest room {room.number} - {room.type or 'Standard'}",
                    "is_active": (room.status != "Deleted" if room.status else True)
                }
                try:
                    location = inventory_crud.create_location(db, location_data)
                    
                    # Link room to location
                    room.inventory_location_id = location.id
                    created_count += 1
                    synced_count += 1
                except Exception as e:
                    db.rollback()
                    # Location might already exist, try to find and link
                    existing = db.query(Location).filter(
                        Location.name == f"Room {room.number}"
                    ).first()
                    if existing and not room.inventory_location_id:
                        room.inventory_location_id = existing.id
                        linked_count += 1
                        synced_count += 1
        
        db.commit()
        
        return {
            "message": "Rooms synchronized successfully",
            "total_rooms": len(rooms),
            "synced": synced_count,
            "locations_created": created_count,
            "rooms_linked": linked_count
        }
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error syncing rooms: {str(e)}")


# Asset Mapping Endpoints
@router.post("/asset-mappings", response_model=AssetMappingOut)
def create_asset_mapping(
    mapping: AssetMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        mapping_data = mapping.model_dump()
        created = inventory_crud.create_asset_mapping(db, mapping_data, assigned_by=current_user.id)
        
        
        # Load relationships for response
        assigner = db.query(User).filter(User.id == created.assigned_by).first()
        item = inventory_crud.get_item_by_id(db, created.item_id)
        location = inventory_crud.get_location_by_id(db, created.location_id)
        
        # Construct location name safely
        location_name = None
        if location:
            if location.building and location.room_area:
                location_name = f"{location.building} - {location.room_area}"
            elif location.building:
                location_name = location.building
            elif location.room_area:
                location_name = location.room_area
            elif hasattr(location, 'name') and location.name:
                location_name = location.name
        
        return {
            "id": created.id,
            "item_id": created.item_id,
            "location_id": created.location_id,
            "serial_number": created.serial_number,
            "assigned_date": created.assigned_date,
            "assigned_by": created.assigned_by,
            "notes": created.notes,
            "is_active": created.is_active,
            "unassigned_date": created.unassigned_date,
            "quantity": created.quantity,
            "assigned_by_name": assigner.name if assigner else None,
            "item_name": item.name if item else None,
            "location_name": location_name
        }
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating asset mapping: {str(e)}")


@router.get("/asset-mappings", response_model=List[AssetMappingOut])
def get_asset_mappings(
    skip: int = 0,
    limit: int = 100,
    location_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Fetch Real Mappings
    real_mappings = inventory_crud.get_all_asset_mappings(db, skip=0, limit=10000, location_id=location_id) # Get all for calculation
    
    # 2. Fetch Location Stock for ALL items (not just fixed assets)
    from app.models.inventory import LocationStock, InventoryItem, Location
    from sqlalchemy import or_
    
    # Filter stocks to exclude inventory points (Warehouses, etc) - ASSETS should be in rooms
    stock_query = db.query(LocationStock).join(InventoryItem).join(Location)
    if location_id:
        stock_query = stock_query.filter(LocationStock.location_id == location_id)
    else:
        # Default: Exclude inventory points, BUT keep Guest Rooms (even if flagged as inventory points)
        stock_query = stock_query.filter(
            or_(
                Location.is_inventory_point == False,
                Location.location_type == "GUEST_ROOM"
            )
        )
        
    stocks = stock_query.all()
    
    # 3. Calculate "Implicit" Mappings (Stock - Mapped)
    stock_map = {} # (location_id, item_id) -> total_stock_qty
    for s in stocks:
        key = (s.location_id, s.item_id)
        stock_map[key] = {
            "qty": s.quantity,
            "stock_obj": s,
            "item": s.item
        }
        
    mapped_qty_map = {} # (location_id, item_id) -> total_mapped_qty
    for m in real_mappings:
        key = (m.location_id, m.item_id)
        mapped_qty_map[key] = mapped_qty_map.get(key, 0) + (m.quantity or 1)
        
    final_list = []
    
    # Add Real Mappings
    for m in real_mappings:
        location = inventory_crud.get_location_by_id(db, m.location_id)
        # Skip if location is inventory point AND NOT a Guest Room (unless specific location requested)
        if not location_id and location and location.is_inventory_point and location.location_type != "GUEST_ROOM":
            continue
            
        assigner = db.query(User).filter(User.id == m.assigned_by).first() if m.assigned_by else None
        item = inventory_crud.get_item_by_id(db, m.item_id)
        
        # Prioritize location.name (e.g., "Room 101"), fallback to building-room_area format
        if location.name:
            location_display = location.name
        elif location.building or location.room_area:
            location_display = f"{location.building} - {location.room_area}"
        else:
            location_display = f"Location {location.id}"
            
        final_list.append({
            **m.__dict__,
            "assigned_by_name": assigner.name if assigner else None,
            "item_name": item.name if item else None,
            "location_name": location_display,
            "is_virtual": False
        })
        
    # Add Virtual Mappings (Implicit)
    for key, data in stock_map.items():
        loc_id, item_id = key
        total_stock = data['qty']
        mapped_total = mapped_qty_map.get(key, 0)
        
        remaining = total_stock - mapped_total
        
        if remaining > 0:
            # Create Virtual Mapping
            s = data['stock_obj']
            item = data['item']
            location = s.location # Relationship should be loaded or fetched
            
            # Ensure location name is available
            if not location:
                location = inventory_crud.get_location_by_id(db, loc_id)
            
            # Prioritize location.name (e.g., "Room 101"), fallback to building-room_area format
            if location.name:
                location_display = location.name
            elif location.building or location.room_area:
                location_display = f"{location.building} - {location.room_area}"
            else:
                location_display = f"Location {location.id}"
                
            final_list.append({
                "id": -s.id, # Negative ID to avoid collision
                "item_id": item_id,
                "location_id": loc_id,
                "item_name": item.name,
                "location_name": location_display,
                "quantity": remaining,
                "assigned_date": s.last_updated,
                "created_at": s.last_updated,
                "updated_at": s.last_updated,
                "notes": "Implicit Assignment (from Stock)",
                "serial_number": None,
                "assigned_by": None,
                "assigned_by_name": "System",
                "status": "active",
                "is_virtual": True
            })
            
    # Sort by recent date
    from datetime import datetime as dt
    final_list.sort(key=lambda x: x.get('created_at') or x.get('assigned_date') or dt.min, reverse=True)
    
    # Apply pagination
    return final_list[skip : skip + limit]


@router.put("/asset-mappings/{mapping_id}", response_model=AssetMappingOut)
def update_asset_mapping(
    mapping_id: int,
    update_data: AssetMappingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    data = update_data.model_dump(exclude_unset=True)
    updated = inventory_crud.update_asset_mapping(db, mapping_id, data)
    
    if not updated:
        raise HTTPException(status_code=404, detail="Asset Mapping not found")
        
    # Load relationships for response
    assigner = db.query(User).filter(User.id == updated.assigned_by).first() if updated.assigned_by else None
    item = inventory_crud.get_item_by_id(db, updated.item_id)
    location = inventory_crud.get_location_by_id(db, updated.location_id)
    
    return {
        **updated.__dict__,
        "assigned_by_name": assigner.name if assigner else None,
        "item_name": item.name if item else None,
        "location_name": f"{location.building} - {location.room_area}" if location else None
    }


@router.delete("/asset-mappings/{mapping_id}")
def unassign_asset(
    mapping_id: int,
    destination_location_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        mapping = inventory_crud.unassign_asset(db, mapping_id, destination_location_id=destination_location_id)
        if not mapping:
            raise HTTPException(status_code=404, detail="Asset mapping not found")
        return {"message": "Asset unassigned successfully"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error unassigning asset: {str(e)}")


# Asset Registry Endpoints (The "Profile" - tracks individual instances)
@router.post("/asset-registry", response_model=AssetRegistryOut)
def create_asset_registry(
    asset: AssetRegistryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    asset_data = asset.model_dump()
    created = inventory_crud.create_asset_registry(db, asset_data, created_by=current_user.id)
    
    # Load relationships for response
    item = inventory_crud.get_item_by_id(db, created.item_id)
    location = inventory_crud.get_location_by_id(db, created.current_location_id) if created.current_location_id else None
    
    return {
        **created.__dict__,
        "item_name": item.name if item else None,
        "current_location_name": f"{location.building} - {location.room_area}" if location else None
    }


@router.get("/asset-registry", response_model=List[AssetRegistryOut])
def get_asset_registry(
    skip: int = 0,
    limit: int = 100,
    location_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    assets = inventory_crud.get_all_asset_registry(db, skip=skip, limit=limit, location_id=location_id, status=status)
    result = []
    for asset in assets:
        item = inventory_crud.get_item_by_id(db, asset.item_id)
        location = inventory_crud.get_location_by_id(db, asset.current_location_id) if asset.current_location_id else None
        result.append({
            **asset.__dict__,
            "item_name": item.name if item else None,
            "current_location_name": f"{location.building} - {location.room_area}" if location else None
        })
    return result


@router.get("/asset-registry/{asset_id}", response_model=AssetRegistryOut)
def get_asset_registry_by_id(asset_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    asset = inventory_crud.get_asset_registry_by_id(db, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    item = inventory_crud.get_item_by_id(db, asset.item_id)
    location = inventory_crud.get_location_by_id(db, asset.current_location_id) if asset.current_location_id else None
    
    return {
        **asset.__dict__,
        "item_name": item.name if item else None,
        "current_location_name": f"{location.building} - {location.room_area}" if location else None
    }


@router.put("/asset-registry/{asset_id}", response_model=AssetRegistryOut)
def update_asset_registry(
    asset_id: int,
    asset_update: AssetRegistryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    asset_data = asset_update.model_dump(exclude_unset=True)
    updated = inventory_crud.update_asset_registry(db, asset_id, asset_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    item = inventory_crud.get_item_by_id(db, updated.item_id)
    location = inventory_crud.get_location_by_id(db, updated.current_location_id) if updated.current_location_id else None
    
    return {
        **updated.__dict__,
        "item_name": item.name if item else None,
        "current_location_name": f"{location.building} - {location.room_area}" if location else None
    }


# Stock Requisition Endpoints
@router.post("/requisitions", response_model=StockRequisitionOut)
def create_stock_requisition(
    requisition: StockRequisitionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return inventory_crud.create_stock_requisition(db, requisition, requested_by_id=current_user.id)


@router.get("/requisitions", response_model=List[StockRequisitionOut])
def get_stock_requisitions(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return inventory_crud.get_all_stock_requisitions(db, skip=skip, limit=limit, status=status)


@router.get("/requisitions/{requisition_id}", response_model=StockRequisitionOut)
def get_stock_requisition(
    requisition_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    requisition = inventory_crud.get_stock_requisition_by_id(db, requisition_id)
    if not requisition:
        raise HTTPException(status_code=404, detail="Requisition not found")
    return requisition


@router.patch("/requisitions/{requisition_id}", response_model=StockRequisitionOut)
def update_stock_requisition(
    requisition_id: int,
    update_data: StockRequisitionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # For now, we only support status update via this endpoint or specific fields
    # If status is in update_data, use the status update logic
    if update_data.status:
        return inventory_crud.update_stock_requisition_status(
            db, requisition_id, update_data.status, approved_by_id=current_user.id if update_data.status == "approved" else None
        )
    return inventory_crud.get_stock_requisition_by_id(db, requisition_id)


@router.patch("/requisitions/{requisition_id}/status", response_model=StockRequisitionOut)
def update_stock_requisition_status(
    requisition_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    updated = inventory_crud.update_stock_requisition_status(
        db, requisition_id, status, approved_by_id=current_user.id if status == "approved" else None
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Requisition not found")
    return updated




@router.get("/issues", response_model=List[StockIssueOut])
def get_stock_issues(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return inventory_crud.get_all_stock_issues(db, skip=skip, limit=limit)

@router.get("/assets/registry", response_model=List[AssetRegistryOut])
def get_all_assets_registry(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all individual fixed asset instances"""
    from app.models.inventory import AssetRegistry
    assets = db.query(AssetRegistry).options(
        joinedload(AssetRegistry.item),
        joinedload(AssetRegistry.current_location)
    ).order_by(AssetRegistry.created_at.desc()).offset(skip).limit(limit).all()
    
    return assets


@router.get("/transactions", response_model=List[InventoryTransactionOut])
def get_all_transactions(
    limit: int = 50,
    skip: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get global transaction history"""
    from app.models.inventory import InventoryTransaction, InventoryItem
    from app.models.user import User
    
    transactions = db.query(InventoryTransaction).options(
        joinedload(InventoryTransaction.item),
        joinedload(InventoryTransaction.user)
    ).order_by(InventoryTransaction.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for txn in transactions:
        result.append({
            **txn.__dict__,
            "item_name": txn.item.name if txn.item else "Unknown Item",
            "created_by_name": txn.user.name if txn.user else "System",
            "unit": txn.item.unit if txn.item else ""
        })
        
    return result


@router.get("/items/{item_id}/transactions", response_model=List[InventoryTransactionOut])
def get_item_transactions(
    item_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Get all transactions for a specific item to show history/audit trail.
    """
    from app.models.inventory import InventoryTransaction, PurchaseMaster
    from app.models.user import User
    
    # Check if item exists
    item = inventory_crud.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    transactions = db.query(InventoryTransaction)\
        .filter(InventoryTransaction.item_id == item_id)\
        .order_by(InventoryTransaction.created_at.desc())\
        .all()
    
    # Enrich with details if needed (User name, Reference context)
    # The response model InventoryTransactionOut should handle basic fields.
    # We might want to ensure 'created_by_name' is populated if the model expects it.
    
    result = []
    for txn in transactions:
        user = db.query(User).filter(User.id == txn.created_by).first() if txn.created_by else None
        
        # Format the result
        result.append({
            **txn.__dict__,
            "created_by_name": user.name if user else "System",
            # We can also add more context about reference (link to PO, etc.)
        })
        
    return result

@router.post("/items/{item_id}/fix-stock", response_model=InventoryItemOut)
def fix_item_stock(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Recalculate item stock based on transaction history and update the current_stock value.
    This fixes discrepancies caused by manual edits or phantom updates.
    """
    from app.models.inventory import InventoryTransaction
    
    item = inventory_crud.get_item_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    # Calculate stock from transaction history
    transactions = db.query(InventoryTransaction).filter(InventoryTransaction.item_id == item_id).all()
    
    calculated_stock = 0.0
    for txn in transactions:
        # Define logic match frontend
        if txn.transaction_type in ["in", "adjustment", "transfer_in"]:
            calculated_stock += txn.quantity
        elif txn.transaction_type in ["out", "transfer_out"]:
            calculated_stock -= txn.quantity
            
    # Update item
    item.current_stock = calculated_stock
    db.commit()
    db.refresh(item)
    
    # Return updated item with category (needed for response model)
    category = inventory_crud.get_category_by_id(db, item.category_id)
    
    return {
        **item.__dict__,
        "category_name": category.name if category else None,
        "department": category.parent_department if category else None,
        "is_low_stock": item.current_stock <= item.min_stock_level if item.min_stock_level else False
    }


@router.post("/adjustments")
def create_stock_adjustment(
    adjustment: StockAdjustmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.inventory import InventoryItem, LocationStock, InventoryTransaction
    
    item = db.query(InventoryItem).filter(InventoryItem.id == adjustment.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    loc_stock = db.query(LocationStock).filter(
        LocationStock.location_id == adjustment.location_id,
        LocationStock.item_id == adjustment.item_id
    ).first()
    
    current_qty = loc_stock.quantity if loc_stock else 0.0
    actual_qty = float(adjustment.actual_stock)
    diff = actual_qty - current_qty
    
    if diff == 0:
        return {"message": "No change in stock", "new_stock": actual_qty}
        
    # Transaction Type logic
    if diff > 0:
        trx_type = "adjustment" # Treated as positive/incoming in recalculate_stock
        direction = "Increased"
    else:
        trx_type = "out" # Treated as negative/outgoing in recalculate_stock
        direction = "Decreased"
    
    trx = InventoryTransaction(
        item_id=adjustment.item_id,
        transaction_type=trx_type,
        quantity=abs(diff),
        unit_price=item.unit_price,
        total_amount=abs(diff) * (item.unit_price or 0) if item.unit_price else 0,
        notes=f"Stock Adjustment by {current_user.name}: {direction} from {current_qty} to {actual_qty}. {adjustment.notes or ''}",
        created_by=current_user.id,
        reference_number=f"ADJ-{datetime.now().strftime('%Y%m%d%H%M')}"
    )
    db.add(trx)
    
    # Update Location Stock
    if loc_stock:
        loc_stock.quantity = actual_qty
        loc_stock.updated_at = datetime.now()
    else:
        new_stock = LocationStock(
            location_id=adjustment.location_id,
            item_id=adjustment.item_id,
            quantity=actual_qty
        )
        db.add(new_stock)
        
    # Update Global Stock
    if item.current_stock is None:
        item.current_stock = 0.0
    item.current_stock += diff
    
    db.commit()
    return {"message": "Stock adjusted successfully", "new_stock": actual_qty}


@router.get("/locations/{location_id}/stock")
def get_location_stock_endpoint(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return inventory_crud.get_location_stock(db, location_id)


@router.get("/recipes")
def get_all_recipes_endpoint(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    recipes = inventory_crud.get_all_recipes(db, skip=skip, limit=limit)
    result = []
    for r in recipes:
        result.append({
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "food_item_name": r.food_item.name if r.food_item else None,
            "servings": float(r.servings or 1),
            "cost_per_serving": float(r.cost_per_serving or 0),
            "ingredients": [
                {
                    "item_name": i.inventory_item.name,
                    "quantity": float(i.quantity),
                    "unit": i.unit,
                    "cost": float(i.cost or 0)
                } for i in r.ingredients if i.inventory_item
            ]
        })
    return result


@router.get("/assets/registry", response_model=List[AssetRegistryOut])
def get_asset_registry(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.inventory import AssetRegistry
    
    query = db.query(AssetRegistry)
    if active_only:
        query = query.filter(AssetRegistry.status != 'written_off')
        
    assets = query.offset(skip).limit(limit).all()
    
    result = []
    for asset in assets:
        result.append({
            **asset.__dict__,
            "item_name": asset.item.name if asset.item else "Unknown Item",
            "item_code": asset.item.item_code if asset.item else None,
            "category": asset.item.category.name if asset.item and asset.item.category else None,
            "location_name": asset.current_location.name if asset.current_location else "Unassigned",
            "purchase_order": asset.purchase_master.purchase_number if asset.purchase_master else None
        })
    return result


# Laundry Endpoints
@router.get("/laundry/items", response_model=List[LaundryLogOut])
def get_laundry_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.inventory import LaundryLog
    from sqlalchemy.orm import joinedload
    
    logs = db.query(LaundryLog).options(
        joinedload(LaundryLog.item),
        joinedload(LaundryLog.source_location)
    ).filter(LaundryLog.status != "Returned").order_by(LaundryLog.sent_at.desc()).all()
    
    result = []
    for log in logs:
        result.append({
            **log.__dict__,
            "item_name": log.item.name if log.item else None,
            "source_location_name": log.source_location.name if log.source_location else (f"Room {log.room_number}" if log.room_number else "Unknown")
        })
    return result


@router.patch("/laundry/{log_id}/status")
def update_laundry_status(
    log_id: int,
    status: str,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.inventory import LaundryLog
    
    log = db.query(LaundryLog).filter(LaundryLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Laundry log not found")
    
    log.status = status
    if notes:
        if log.notes:
            log.notes += f" | {notes}"
        else:
            log.notes = notes
    
    if status == "Washed":
        log.washed_at = datetime.utcnow()
    elif status == "Returned":
        log.returned_at = datetime.utcnow()
        
    db.commit()
    return {"message": f"Laundry status updated to {status}"}


@router.post("/laundry/return-items")
def return_laundry_items(
    log_id: int,
    target_location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.inventory import LaundryLog, LocationStock, InventoryTransaction, Location
    
    log = db.query(LaundryLog).filter(LaundryLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Laundry log not found")
    
    # 1. Find Laundry Location
    laundry_loc = db.query(Location).filter(Location.location_type == "LAUNDRY").first()
    if not laundry_loc:
         raise HTTPException(status_code=400, detail="Laundry location not found")

    # 2. Update stock: Move from Laundry to target
    # Decrease Laundry stock
    laundry_stock = db.query(LocationStock).filter(
        LocationStock.location_id == laundry_loc.id,
        LocationStock.item_id == log.item_id
    ).first()
    
    if laundry_stock:
        laundry_stock.quantity = max(0, laundry_stock.quantity - log.quantity)
    
    # Increase Target stock
    target_stock = db.query(LocationStock).filter(
        LocationStock.location_id == target_location_id,
        LocationStock.item_id == log.item_id
    ).first()
    
    if not target_stock:
        target_stock = LocationStock(
            location_id=target_location_id,
            item_id=log.item_id,
            quantity=0
        )
        db.add(target_stock)
    
    target_stock.quantity += log.quantity
    
    # 3. Update Log
    log.status = "Returned"
    log.returned_at = datetime.utcnow()
    
    # 4. Transaction
    target_loc = db.query(Location).filter(Location.id == target_location_id).first()
    target_name = target_loc.name if target_loc else f"Location {target_location_id}"
    
    transaction = InventoryTransaction(
        item_id=log.item_id,
        transaction_type="transfer",
        quantity=log.quantity,
        unit_price=0.0,
        reference_number=f"LAUNDRY-RET-{log.id}",
        notes=f"Returned from Laundry to {target_name}",
        created_by=current_user.id
    )
    db.add(transaction)
    
    db.commit()
    return {"message": "Items returned from laundry successfully"}
