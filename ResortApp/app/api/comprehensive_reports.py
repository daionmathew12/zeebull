"""
Comprehensive Reports API
Includes reports for: Inventory (Category/Department), Bookings, Package Bookings,
Expenses, Food Orders, Purchases, Vendors, Services
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, case
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from pydantic import BaseModel
from app.database import get_db
from app.utils.auth import get_current_user
from app.models.user import User
from app.models.booking import Booking, BookingRoom
from app.models.Package import PackageBooking, PackageBookingRoom, Package
from app.models.expense import Expense
from app.models.foodorder import FoodOrder, FoodOrderItem
from app.models.food_item import FoodItem
from app.models.inventory import (
    InventoryItem, InventoryCategory, PurchaseMaster, PurchaseDetail, Vendor, Location
)
from app.models.service import AssignedService, Service
from app.models.room import Room
from app.models.employee import Employee
from app.utils.api_optimization import apply_api_optimizations
from app.utils.branch_scope import get_branch_id

router = APIRouter(prefix="/reports/comprehensive", tags=["Comprehensive Reports"])


# ==================== SCHEMAS ====================

class InventoryCategoryReport(BaseModel):
    category_id: int
    category_name: str
    total_items: int
    total_quantity: float
    total_value: float
    low_stock_items: int

class InventoryDepartmentReport(BaseModel):
    department: str
    total_items: int
    total_quantity: float
    total_value: float

class BookingReport(BaseModel):
    booking_id: int
    guest_name: str
    check_in: date
    check_out: date
    room_numbers: List[str]
    total_amount: float
    status: str
    booking_date: datetime

class PackageBookingReport(BaseModel):
    package_booking_id: int
    guest_name: str
    package_name: str
    check_in: date
    check_out: date
    room_numbers: List[str]
    package_price: float
    status: str
    booking_date: datetime

class ExpenseReport(BaseModel):
    expense_id: int
    category: str
    description: str
    amount: float
    expense_date: date
    vendor_name: Optional[str]
    payment_method: str

class FoodOrderReport(BaseModel):
    order_id: int
    room_number: str
    guest_name: str
    order_date: datetime
    total_amount: float
    items_count: int
    status: str

class PurchaseReport(BaseModel):
    purchase_id: int
    vendor_name: str
    invoice_number: str
    purchase_date: date
    total_amount: float
    items_count: int
    payment_status: str

class VendorReport(BaseModel):
    vendor_id: int
    vendor_name: str
    contact_person: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    total_purchases: int
    total_amount: float
    last_purchase_date: Optional[date]

class ServiceReport(BaseModel):
    service_id: int
    service_name: str
    total_assignments: int
    total_revenue: float
    completed_count: int
    pending_count: int


# ==================== INVENTORY REPORTS ====================

@router.get("/inventory/category-wise")
@apply_api_optimizations
def get_inventory_category_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    branch_id: int | None = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """Inventory report grouped by category"""
    try:
        query = db.query(
            InventoryCategory.id,
            InventoryCategory.name,
            func.count(InventoryItem.id).label('total_items'),
            func.coalesce(func.sum(InventoryItem.current_stock), 0).label('total_quantity'),
            func.coalesce(func.sum(InventoryItem.current_stock * InventoryItem.unit_price), 0).label('total_value'),
            func.sum(case([(InventoryItem.current_stock <= InventoryItem.min_stock_level, 1)], else_=0)).label('low_stock')
        ).join(
            InventoryItem, InventoryItem.category_id == InventoryCategory.id
        )
        
        # Skip InventoryItem filtering by branch_id as it is now global
        # if branch_id:
        #     query = query.filter(InventoryItem.branch_id == branch_id)
            
        query = query.group_by(InventoryCategory.id, InventoryCategory.name)
        
        results = query.all()
        
        return [
            {
                "category_id": r.id,
                "category_name": r.name,
                "total_items": r.total_items,
                "total_quantity": float(r.total_quantity or 0),
                "total_value": float(r.total_value or 0),
                "low_stock_items": r.low_stock or 0
            }
            for r in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating inventory category report: {str(e)}")


@router.get("/inventory/department-wise")
@apply_api_optimizations
def get_inventory_department_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    branch_id: int | None = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """Inventory report grouped by department/location"""
    try:
        query = db.query(
            Location.name.label('department'),
            func.count(InventoryItem.id).label('total_items'),
            func.coalesce(func.sum(InventoryItem.current_stock), 0).label('total_quantity'),
            func.coalesce(func.sum(InventoryItem.current_stock * InventoryItem.unit_price), 0).label('total_value')
        ).join(
            InventoryItem, InventoryItem.location_id == Location.id
        )
        
        # Skip Location filtering by branch_id if we want global items from all locations? 
        # Actually Location IS branch-dependent, so filtering by Location.branch_id is correct.
        if branch_id:
            query = query.filter(Location.branch_id == branch_id)
            
        query = query.group_by(Location.name)
        
        results = query.all()
        
        return [
            {
                "department": r.department,
                "total_items": r.total_items,
                "total_quantity": float(r.total_quantity or 0),
                "total_value": float(r.total_value or 0)
            }
            for r in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating inventory department report: {str(e)}")


# ==================== BOOKING REPORTS ====================

@router.get("/bookings")
@apply_api_optimizations
def get_bookings_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    branch_id: int | None = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """Comprehensive bookings report"""
    try:
        query = (db.query(Booking).filter(Booking.branch_id == branch_id) if branch_id is not None else db.query(Booking)).options(
            joinedload(Booking.rooms).joinedload(BookingRoom.room)
        )
        
        if branch_id:
            query = query.filter(Booking.branch_id == branch_id)
        
        if start_date:
            query = query.filter(Booking.check_in >= start_date)
        if end_date:
            query = query.filter(Booking.check_in <= end_date)
        if status:
            query = query.filter(Booking.status == status)
        
        bookings = query.order_by(Booking.check_in.desc()).limit(1000).all()
        
        results = []
        for booking in bookings:
            room_numbers = [br.room.number for br in booking.rooms if br.room]
            # Calculate total amount (room charges + estimated extras)
            total_amount = sum([br.room.price_per_night or 0 for br in booking.rooms if br.room]) * (
                (booking.check_out - booking.check_in).days if booking.check_out and booking.check_in else 1
            )
            
            results.append({
                "booking_id": booking.id,
                "guest_name": booking.guest_name,
                "check_in": booking.check_in,
                "check_out": booking.check_out,
                "room_numbers": room_numbers,
                "total_amount": float(total_amount),
                "status": booking.status,
                "booking_date": booking.created_at
            })
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating bookings report: {str(e)}")


# ==================== PACKAGE BOOKING REPORTS ====================

@router.get("/package-bookings")
@apply_api_optimizations
def get_package_bookings_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    branch_id: int | None = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """Comprehensive package bookings report"""
    try:
        query = (db.query(PackageBooking).filter(PackageBooking.branch_id == branch_id) if branch_id is not None else db.query(PackageBooking)).options(
            joinedload(PackageBooking.rooms).joinedload(PackageBookingRoom.room),
            joinedload(PackageBooking.package)
        )
        
        if branch_id:
            query = query.filter(PackageBooking.branch_id == branch_id)
        
        if start_date:
            query = query.filter(PackageBooking.check_in >= start_date)
        if end_date:
            query = query.filter(PackageBooking.check_in <= end_date)
        if status:
            query = query.filter(PackageBooking.status == status)
        
        package_bookings = query.order_by(PackageBooking.check_in.desc()).limit(1000).all()
        
        results = []
        for pb in package_bookings:
            room_numbers = [pbr.room.number for pbr in pb.rooms if pbr.room]
            
            results.append({
                "package_booking_id": pb.id,
                "guest_name": pb.guest_name,
                "package_name": pb.package.name if pb.package else "Unknown",
                "check_in": pb.check_in,
                "check_out": pb.check_out,
                "room_numbers": room_numbers,
                "package_price": float(pb.package.price if pb.package and pb.package.price else 0),
                "status": pb.status,
                "booking_date": pb.created_at
            })
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating package bookings report: {str(e)}")


# ==================== EXPENSE REPORTS ====================

@router.get("/expenses")
@apply_api_optimizations
def get_expenses_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    branch_id: int | None = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """Comprehensive expenses report"""
    try:
        query = (db.query(Expense).filter(Expense.branch_id == branch_id) if branch_id is not None else db.query(Expense)).options(
            joinedload(Expense.vendor)
        )
        
        if branch_id:
            query = query.filter(Expense.branch_id == branch_id)
        
        if start_date:
            query = query.filter(Expense.expense_date >= start_date)
        if end_date:
            query = query.filter(Expense.expense_date <= end_date)
        if category:
            query = query.filter(Expense.category == category)
        
        expenses = query.order_by(Expense.expense_date.desc()).limit(1000).all()
        
        return [
            {
                "expense_id": e.id,
                "category": e.category,
                "description": e.description,
                "amount": float(e.amount),
                "expense_date": e.expense_date,
                "vendor_name": e.vendor.name if e.vendor else None,
                "payment_method": e.payment_method or "cash"
            }
            for e in expenses
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating expenses report: {str(e)}")


# ==================== FOOD ORDER REPORTS ====================

@router.get("/food-orders")
@apply_api_optimizations
def get_food_orders_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    room_number: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    branch_id: int | None = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """Comprehensive food orders report"""
    try:
        query = (db.query(FoodOrder).filter(FoodOrder.branch_id == branch_id) if branch_id is not None else db.query(FoodOrder)).options(
            joinedload(FoodOrder.room),
            joinedload(FoodOrder.items).joinedload(FoodOrderItem.food_item)
        )
        
        if branch_id:
            query = query.filter(FoodOrder.branch_id == branch_id)
        
        if start_date:
            query = query.filter(func.date(FoodOrder.created_at) >= start_date)
        if end_date:
            query = query.filter(func.date(FoodOrder.created_at) <= end_date)
        if room_number:
            room = db.query(Room).filter(Room.number == room_number).first()
            if room:
                query = query.filter(FoodOrder.room_id == room.id)
        
        orders = query.order_by(FoodOrder.created_at.desc()).limit(1000).all()
        
        return [
            {
                "order_id": o.id,
                "room_number": o.room.number if o.room else "N/A",
                "guest_name": o.guest_name or "N/A",
                "order_date": o.created_at,
                "total_amount": float(o.amount or 0),
                "items_count": len(o.items) if o.items else 0,
                "status": o.status or "pending"
            }
            for o in orders
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating food orders report: {str(e)}")


# ==================== PURCHASE REPORTS ====================

@router.get("/purchases")
@apply_api_optimizations
def get_purchases_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    vendor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    branch_id: int | None = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """Comprehensive purchases report"""
    try:
        query = (db.query(PurchaseMaster).filter(PurchaseMaster.branch_id == branch_id) if branch_id is not None else db.query(PurchaseMaster)).options(
            joinedload(PurchaseMaster.vendor),
            joinedload(PurchaseMaster.details)
        )
        
        if branch_id:
            query = query.filter(PurchaseMaster.branch_id == branch_id)
        
        if start_date:
            query = query.filter(PurchaseMaster.purchase_date >= start_date)
        if end_date:
            query = query.filter(PurchaseMaster.purchase_date <= end_date)
        if vendor_id:
            query = query.filter(PurchaseMaster.vendor_id == vendor_id)
        
        purchases = query.order_by(PurchaseMaster.purchase_date.desc()).limit(1000).all()
        
        return [
            {
                "purchase_id": p.id,
                "vendor_name": p.vendor.name if p.vendor else "Unknown",
                "invoice_number": p.invoice_number or "N/A",
                "purchase_date": p.purchase_date,
                "total_amount": float(p.total_amount or 0),
                "items_count": len(p.details) if p.details else 0,
                "payment_status": p.payment_status or "pending"
            }
            for p in purchases
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating purchases report: {str(e)}")


# ==================== VENDOR REPORTS ====================

@router.get("/vendors")
@apply_api_optimizations
def get_vendors_report(
    db: Session = Depends(get_db),
    branch_id: int | None = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """Comprehensive vendors report with purchase statistics"""
    try:
        query = db.query(Vendor).options(
            joinedload(Vendor.purchases)
        )
        
        # Skip Vendor filtering by branch_id if Vendors are global? 
        # Actually Vendors are still branch-dependent in the current model.
        if branch_id:
            query = query.filter(Vendor.branch_id == branch_id)
            
        vendors = query.limit(500).all()
        
        results = []
        for vendor in vendors:
            purchases = vendor.purchases or []
            total_amount = sum([float(p.total_amount or 0) for p in purchases])
            last_purchase = max([p.purchase_date for p in purchases], default=None) if purchases else None
            
            results.append({
                "vendor_id": vendor.id,
                "vendor_name": vendor.name,
                "contact_person": vendor.contact_person,
                "phone": vendor.phone,
                "email": vendor.email,
                "total_purchases": len(purchases),
                "total_amount": float(total_amount),
                "last_purchase_date": last_purchase
            })
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating vendors report: {str(e)}")


# ==================== SERVICE REPORTS ====================

@router.get("/services")
@apply_api_optimizations
def get_services_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    branch_id: int | None = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """Comprehensive services report"""
    try:
        query = db.query(Service).options(
            joinedload(Service.assigned_services)
        )
        
        if branch_id:
            query = query.filter(Service.branch_id == branch_id)
        
        services = query.limit(500).all()
        
        results = []
        for service in services:
            assigned = service.assigned_services or []
            
            # Filter by date if provided
            if start_date or end_date:
                filtered_assigned = []
                for a in assigned:
                    if start_date and a.assigned_at and a.assigned_at.date() < start_date:
                        continue
                    if end_date and a.assigned_at and a.assigned_at.date() > end_date:
                        continue
                    filtered_assigned.append(a)
                assigned = filtered_assigned
            
            total_revenue = sum([float(a.service.charges or 0) for a in assigned if a.service])
            completed = len([a for a in assigned if a.status == "completed"])
            pending = len([a for a in assigned if a.status == "pending" or a.status == "in_progress"])
            
            results.append({
                "service_id": service.id,
                "service_name": service.name,
                "total_assignments": len(assigned),
                "total_revenue": float(total_revenue),
                "completed_count": completed,
                "pending_count": pending
            })
        
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating services report: {str(e)}")


# ==================== SUMMARY ENDPOINT ====================

@router.get("/summary")
@apply_api_optimizations
def get_comprehensive_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    branch_id: int | None = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """Get summary statistics for all reports"""
    try:
        # Date filters
        date_filter = []
        if branch_id:
            # Skip InventoryItem filtering by branch_id as it is now global
            pass
        
        if start_date:
            date_filter.append(func.date(Booking.check_in) >= start_date)
        if end_date:
            date_filter.append(func.date(Booking.check_in) <= end_date)
        
        # Bookings summary
        bookings_query = db.query(func.count(Booking.id), func.coalesce(func.sum(
            case((Booking.check_out.isnot(None), 
                  (Booking.check_out - Booking.check_in).days * 1000), else_=0)
        ), 0))
        if date_filter:
            bookings_query = bookings_query.filter(and_(*date_filter))
        bookings_count, bookings_revenue = bookings_query.first()
        
        # Package bookings summary
        pkg_date_filter = []
        if start_date:
            pkg_date_filter.append(func.date(PackageBooking.check_in) >= start_date)
        if end_date:
            pkg_date_filter.append(func.date(PackageBooking.check_in) <= end_date)
        
        pkg_bookings_query = db.query(func.count(PackageBooking.id), func.coalesce(
            func.sum(Package.price), 0
        )).join(Package, PackageBooking.package_id == Package.id)
        if branch_id:
            pkg_bookings_query = pkg_bookings_query.filter(PackageBooking.branch_id == branch_id)
        if pkg_date_filter:
            pkg_bookings_query = pkg_bookings_query.filter(and_(*pkg_date_filter))
        pkg_count, pkg_revenue = pkg_bookings_query.first()
        
        # Expenses summary
        exp_date_filter = []
        if branch_id:
            exp_date_filter.append(Expense.branch_id == branch_id)
        if start_date:
            exp_date_filter.append(Expense.expense_date >= start_date)
        if end_date:
            exp_date_filter.append(Expense.expense_date <= end_date)
        
        expenses_query = db.query(func.count(Expense.id), func.coalesce(func.sum(Expense.amount), 0))
        if exp_date_filter:
            expenses_query = expenses_query.filter(and_(*exp_date_filter))
        expenses_count, expenses_total = expenses_query.first()
        
        # Food orders summary
        food_date_filter = []
        if branch_id:
            food_date_filter.append(FoodOrder.branch_id == branch_id)
        if start_date:
            food_date_filter.append(func.date(FoodOrder.created_at) >= start_date)
        if end_date:
            food_date_filter.append(func.date(FoodOrder.created_at) <= end_date)
        
        food_query = db.query(func.count(FoodOrder.id), func.coalesce(func.sum(FoodOrder.amount), 0))
        if food_date_filter:
            food_query = food_query.filter(and_(*food_date_filter))
        food_count, food_revenue = food_query.first()
        
        # Purchases summary
        purchase_date_filter = []
        if branch_id:
            purchase_date_filter.append(PurchaseMaster.branch_id == branch_id)
        if start_date:
            purchase_date_filter.append(PurchaseMaster.purchase_date >= start_date)
        if end_date:
            purchase_date_filter.append(PurchaseMaster.purchase_date <= end_date)
        
        purchase_query = db.query(func.count(PurchaseMaster.id), func.coalesce(func.sum(PurchaseMaster.total_amount), 0))
        if purchase_date_filter:
            purchase_query = purchase_query.filter(and_(*purchase_date_filter))
        purchase_count, purchase_total = purchase_query.first()
        
        # Services summary
        service_query = db.query(func.count(Service.id))
        assigned_query = db.query(func.count(AssignedService.id))
        if branch_id:
            service_query = service_query.filter(Service.branch_id == branch_id)
            assigned_query = assigned_query.filter(AssignedService.branch_id == branch_id)
        service_count = service_query.scalar() or 0
        assigned_count = assigned_query.scalar() or 0
        
        # Inventory summary
        inv_item_query = db.query(func.count(InventoryItem.id))
        inv_val_query = db.query(func.coalesce(func.sum(InventoryItem.current_stock * InventoryItem.unit_price), 0))
        if branch_id:
            # Skip InventoryItem filtering by branch_id as it is now global
            pass
        inventory_items = inv_item_query.scalar() or 0
        inventory_value = inv_val_query.scalar() or 0
        
        # Vendors summary
        vendor_query = db.query(func.count(Vendor.id))
        if branch_id:
            vendor_query = vendor_query.filter(Vendor.branch_id == branch_id)
        vendor_count = vendor_query.scalar() or 0
        
        return {
            "bookings": {
                "count": bookings_count or 0,
                "revenue": float(bookings_revenue or 0)
            },
            "package_bookings": {
                "count": pkg_count or 0,
                "revenue": float(pkg_revenue or 0)
            },
            "expenses": {
                "count": expenses_count or 0,
                "total": float(expenses_total or 0)
            },
            "food_orders": {
                "count": food_count or 0,
                "revenue": float(food_revenue or 0)
            },
            "purchases": {
                "count": purchase_count or 0,
                "total": float(purchase_total or 0)
            },
            "services": {
                "total_services": service_count,
                "total_assignments": assigned_count
            },
            "inventory": {
                "total_items": inventory_items,
                "total_value": float(inventory_value or 0)
            },
            "vendors": {
                "count": vendor_count
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

