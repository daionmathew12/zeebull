"""
Comprehensive Reporting Module for Resort Management Application
Organized by Department: Front Office, Restaurant, Inventory, Housekeeping, Accounts, Security/HR, Management Dashboard
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, and_, or_, case, cast, Date, extract
from datetime import datetime, date, timedelta
from typing import Optional, List
from decimal import Decimal

from app.database import get_db
from app.utils.auth import get_current_user
from app.models import (
    Booking, BookingRoom, PackageBooking, PackageBookingRoom,
    Checkout,
    FoodOrder, FoodOrderItem, FoodItem,
    InventoryItem, InventoryCategory, InventoryTransaction, PurchaseMaster, PurchaseDetail, WasteLog,
    Expense, Employee, Attendance,
    Room, Service, AssignedService, Vendor
)
from app.models.checkout import CheckoutPayment, CheckoutVerification
from app.models.employee import WorkingLog, Leave
from app.utils.api_optimization import apply_api_optimizations

router = APIRouter(prefix="/reports", tags=["Reports"])


# ============================================
# 1. 🏨 FRONT OFFICE REPORTS
# ============================================

@router.get("/front-office/daily-arrival")
@apply_api_optimizations
def get_daily_arrival_report(
    report_date: Optional[date] = Query(None, description="Date for arrival report (default: today)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Daily Arrival Report: List of guests checking in today"""
    try:
        if not report_date:
            report_date = date.today()
        
        bookings = db.query(Booking).filter(
            Booking.check_in == report_date
        ).options(
            joinedload(Booking.booking_rooms).joinedload(BookingRoom.room),
            joinedload(Booking.user)
        ).offset(skip).limit(limit).all()
        
        package_bookings = db.query(PackageBooking).filter(
            PackageBooking.check_in == report_date
        ).options(
            joinedload(PackageBooking.rooms).joinedload(PackageBookingRoom.room),
            joinedload(PackageBooking.user),
            joinedload(PackageBooking.package)
        ).offset(skip).limit(limit).all()
        
        result = []
        for booking in bookings:
            for br in booking.booking_rooms:
                result.append({
                    "guest_name": booking.guest_name,
                    "guest_mobile": booking.guest_mobile,
                    "guest_email": booking.guest_email,
                    "room_number": br.room.number if br.room else "N/A",
                    "room_type": br.room.type if br.room else "N/A",
                    "adults": booking.adults,
                    "children": booking.children,
                    "advance_paid": booking.advance_deposit,
                    "total_amount": booking.total_amount,
                    "special_requests": booking.guest_email,  # Can be enhanced with a notes field
                    "booking_type": "Regular"
                })
        
        for pkg_booking in package_bookings:
            # Calculate total amount dynamically if missing
            calculated_total = 0.0
            if hasattr(pkg_booking, 'total_amount'):
                calculated_total = pkg_booking.total_amount
            elif pkg_booking.package:
                # Basic calculation: Price per night * nights * rooms
                try:
                    check_in = pkg_booking.check_in
                    check_out = pkg_booking.check_out
                    nights = (check_out - check_in).days
                    nights = max(1, nights)
                    num_rooms = len(pkg_booking.rooms) if pkg_booking.rooms else 1
                    calculated_total = pkg_booking.package.price * nights * num_rooms
                except:
                    calculated_total = 0.0

            package_title = pkg_booking.package.title if pkg_booking.package else 'N/A'

            for pbr in pkg_booking.rooms:
                result.append({
                    "guest_name": pkg_booking.guest_name,
                    "guest_mobile": pkg_booking.guest_mobile,
                    "guest_email": pkg_booking.guest_email,
                    "room_number": pbr.room.number if pbr.room else "N/A",
                    "room_type": pbr.room.type if pbr.room else "N/A",
                    "adults": pkg_booking.adults,
                    "children": pkg_booking.children,
                    "advance_paid": pkg_booking.advance_deposit,
                    "total_amount": calculated_total,
                    "special_requests": f"Package: {package_title}",
                    "booking_type": "Package"
                })
        
        return {"date": report_date.isoformat(), "arrivals": result, "total": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching daily arrival report: {str(e)}")


@router.get("/front-office/daily-departure")
@apply_api_optimizations
def get_daily_departure_report(
    report_date: Optional[date] = Query(None, description="Date for departure report (default: today)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Daily Departure Report: List of guests checking out"""
    if not report_date:
        report_date = date.today()
    
    checkouts = db.query(Checkout).filter(
        func.date(Checkout.checkout_date) == report_date
    ).options(
        joinedload(Checkout.booking),
        joinedload(Checkout.package_booking),
        joinedload(Checkout.payments)
    ).offset(skip).limit(limit).all()
    
    result = []
    for checkout in checkouts:
        balance_pending = checkout.grand_total - sum(p.amount for p in checkout.payments)
        result.append({
            "room_number": checkout.room_number,
            "guest_name": checkout.guest_name,
            "checkout_time": checkout.checkout_date.isoformat() if checkout.checkout_date else None,
            "room_total": checkout.room_total,
            "food_total": checkout.food_total,
            "service_total": checkout.service_total,
            "grand_total": checkout.grand_total,
            "advance_deposit": checkout.advance_deposit,
            "balance_pending": balance_pending,
            "payment_method": checkout.payment_method,
            "invoice_number": checkout.invoice_number,
            "billing_instructions": "Standard checkout"  # Can be enhanced
        })
    
    return {"date": report_date.isoformat(), "departures": result, "total": len(result)}


@router.get("/front-office/occupancy")
@apply_api_optimizations
def get_occupancy_report(
    report_date: Optional[date] = Query(None, description="Date for occupancy report (default: today)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Occupancy Report: % of rooms occupied vs vacant"""
    if not report_date:
        report_date = date.today()
    
    total_rooms = db.query(Room).count()
    
    # Occupied rooms (checked in but not checked out)
    occupied_bookings = db.query(Booking).filter(
        and_(
            Booking.check_in <= report_date,
            Booking.check_out > report_date,
            Booking.status.in_(["checked-in", "booked"])
        )
    ).count()
    
    occupied_packages = db.query(PackageBooking).filter(
        and_(
            PackageBooking.check_in <= report_date,
            PackageBooking.check_out > report_date,
            PackageBooking.status.in_(["checked-in", "booked"])
        )
    ).count()
    
    occupied_rooms = occupied_bookings + occupied_packages
    vacant_rooms = total_rooms - occupied_rooms
    occupancy_percentage = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0
    
    return {
        "date": report_date.isoformat(),
        "total_rooms": total_rooms,
        "occupied_rooms": occupied_rooms,
        "vacant_rooms": vacant_rooms,
        "occupancy_percentage": round(occupancy_percentage, 2)
    }


@router.get("/front-office/police-c-form")
@apply_api_optimizations
def get_police_c_form_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Police / C-Form Report: List of foreign nationals (Legal Requirement)"""
    # Note: This requires passport/visa fields in Booking model
    # For now, returning all bookings - can be filtered by nationality when field is added
    query = db.query(Booking).filter(Booking.status.in_(["checked-in", "booked"]))
    
    if start_date:
        query = query.filter(Booking.check_in >= start_date)
    if end_date:
        query = query.filter(Booking.check_in <= end_date)
    
    bookings = query.options(
        joinedload(Booking.booking_rooms).joinedload(BookingRoom.room)
    ).offset(skip).limit(limit).all()
    
    result = []
    for booking in bookings:
        result.append({
            "guest_name": booking.guest_name,
            "guest_mobile": booking.guest_mobile,
            "guest_email": booking.guest_email,
            "check_in": booking.check_in.isoformat(),
            "check_out": booking.check_out.isoformat(),
            "passport_number": "N/A",  # Add passport field to Booking model
            "visa_number": "N/A",  # Add visa field to Booking model
            "nationality": "N/A",  # Add nationality field to Booking model
            "rooms": [br.room.number if br.room else "N/A" for br in booking.booking_rooms]
        })
    
    return {"foreign_nationals": result, "total": len(result)}


@router.get("/front-office/night-audit")
@apply_api_optimizations
def get_night_audit_report(
    audit_date: Optional[date] = Query(None, description="Date for night audit (default: yesterday)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Night Audit Report: Summary of day's total business closed at midnight"""
    if not audit_date:
        audit_date = date.today() - timedelta(days=1)
    
    # Room revenue
    room_revenue = db.query(func.sum(Checkout.room_total)).filter(
        func.date(Checkout.checkout_date) == audit_date
    ).scalar() or 0
    
    # Food & Beverage revenue
    food_revenue = db.query(func.sum(Checkout.food_total)).filter(
        func.date(Checkout.checkout_date) == audit_date
    ).scalar() or 0
    
    # Service revenue
    service_revenue = db.query(func.sum(Checkout.service_total)).filter(
        func.date(Checkout.checkout_date) == audit_date
    ).scalar() or 0
    
    # Tax collected
    tax_collected = db.query(func.sum(Checkout.tax_amount)).filter(
        func.date(Checkout.checkout_date) == audit_date
    ).scalar() or 0
    
    # Total revenue
    total_revenue = room_revenue + food_revenue + service_revenue + tax_collected
    
    # Checkouts count
    checkouts_count = db.query(Checkout).filter(
        func.date(Checkout.checkout_date) == audit_date
    ).count()
    
    return {
        "audit_date": audit_date.isoformat(),
        "room_revenue": float(room_revenue),
        "food_beverage_revenue": float(food_revenue),
        "service_revenue": float(service_revenue),
        "tax_collected": float(tax_collected),
        "total_revenue": float(total_revenue),
        "checkouts_count": checkouts_count
    }


@router.get("/front-office/no-show-cancellation")
@apply_api_optimizations
def get_no_show_cancellation_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """No-Show & Cancellation Report: Revenue loss tracking"""
    query = db.query(Booking).filter(
        Booking.status.in_(["cancelled", "no-show"])
    )
    
    if start_date:
        query = query.filter(Booking.check_in >= start_date)
    if end_date:
        query = query.filter(Booking.check_in <= end_date)
    
    bookings = query.options(
        joinedload(Booking.booking_rooms).joinedload(BookingRoom.room)
    ).offset(skip).limit(limit).all()
    
    result = []
    total_revenue_loss = 0
    for booking in bookings:
        revenue_loss = booking.total_amount - booking.advance_deposit
        total_revenue_loss += revenue_loss
        result.append({
            "guest_name": booking.guest_name,
            "check_in": booking.check_in.isoformat(),
            "check_out": booking.check_out.isoformat(),
            "status": booking.status,
            "total_amount": booking.total_amount,
            "advance_deposit": booking.advance_deposit,
            "revenue_loss": revenue_loss,
            "rooms": [br.room.number if br.room else "N/A" for br in booking.booking_rooms]
        })
    
    return {
        "no_shows_cancellations": result,
        "total_revenue_loss": float(total_revenue_loss),
        "total_count": len(result)
    }


@router.get("/front-office/in-house-guests")
@apply_api_optimizations
def get_in_house_guest_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """In-House Guest List: Currently checked-in guests (Emergency evacuation list)"""
    try:
        today = date.today()
        
        bookings = db.query(Booking).filter(
            and_(
                Booking.check_in <= today,
                Booking.check_out > today,
                Booking.status == "checked-in"
            )
        ).options(
            joinedload(Booking.booking_rooms).joinedload(BookingRoom.room)
        ).offset(skip).limit(limit).all()
        
        package_bookings = db.query(PackageBooking).filter(
            and_(
                PackageBooking.check_in <= today,
                PackageBooking.check_out > today,
                PackageBooking.status == "checked-in"
            )
        ).options(
            joinedload(PackageBooking.rooms).joinedload(PackageBookingRoom.room),
            joinedload(PackageBooking.package)
        ).offset(skip).limit(limit).all()
        
        result = []
        for booking in bookings:
            for br in booking.booking_rooms:
                result.append({
                    "guest_name": booking.guest_name,
                    "guest_mobile": booking.guest_mobile,
                    "room_number": br.room.number if br.room else "N/A",
                    "check_in": booking.check_in.isoformat(),
                    "check_out": booking.check_out.isoformat(),
                    "adults": booking.adults,
                    "children": booking.children,
                    "booking_type": "Regular"
                })
        
        for pkg_booking in package_bookings:
            for pbr in pkg_booking.rooms:
                result.append({
                    "guest_name": pkg_booking.guest_name,
                    "guest_mobile": pkg_booking.guest_mobile,
                    "room_number": pbr.room.number if pbr.room else "N/A",
                    "check_in": pkg_booking.check_in.isoformat(),
                    "check_out": pkg_booking.check_out.isoformat(),
                    "adults": pkg_booking.adults,
                    "children": pkg_booking.children,
                    "booking_type": "Package"
                })
        
        return {"in_house_guests": result, "total": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching in-house guests: {str(e)}")


# ============================================
# 2. 🥘 RESTAURANT (F&B) REPORTS
# ============================================

@router.get("/restaurant/daily-sales-summary")
@apply_api_optimizations
def get_daily_sales_summary(
    report_date: Optional[date] = Query(None, description="Date for sales summary (default: today)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Daily Sales Summary: Food vs Beverage vs Alcohol sales by meal period"""
    if not report_date:
        report_date = date.today()
    
    # Get all food orders for the date
    orders = db.query(FoodOrder).filter(
        func.date(FoodOrder.created_at) == report_date
    ).options(
        joinedload(FoodOrder.items).joinedload(FoodOrderItem.food_item)
    ).all()
    
    food_sales = 0
    beverage_sales = 0
    alcohol_sales = 0
    
    breakfast_total = 0
    lunch_total = 0
    dinner_total = 0
    
    for order in orders:
        order_total = order.amount or 0
        hour = order.created_at.hour if order.created_at else 12
        
        # Categorize by meal period
        if 6 <= hour < 11:
            breakfast_total += order_total
        elif 11 <= hour < 16:
            lunch_total += order_total
        elif 16 <= hour < 23:
            dinner_total += order_total
        
        # Categorize by item type (requires FoodItem.category field)
        for item in order.items:
            if item.food_item:
                # Assuming category field exists - adjust based on actual model
                category = getattr(item.food_item, 'category', None)
                item_total = (item.food_item.price or 0) * (item.quantity or 0)
                
                if category == "Beverage" or "drink" in (item.food_item.name or "").lower():
                    beverage_sales += item_total
                elif category == "Alcohol" or "alcohol" in (item.food_item.name or "").lower():
                    alcohol_sales += item_total
                else:
                    food_sales += item_total
    
    return {
        "date": report_date.isoformat(),
        "food_sales": float(food_sales),
        "beverage_sales": float(beverage_sales),
        "alcohol_sales": float(alcohol_sales),
        "breakfast_sales": float(breakfast_total),
        "lunch_sales": float(lunch_total),
        "dinner_sales": float(dinner_total),
        "total_sales": float(food_sales + beverage_sales + alcohol_sales)
    }


@router.get("/restaurant/item-wise-sales")
@apply_api_optimizations
def get_item_wise_sales_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Item-wise Sales Report: Which dish is selling the most?"""
    query = db.query(
        FoodItem.id,
        FoodItem.name,
        func.sum(FoodOrderItem.quantity).label("total_quantity"),
        func.sum(FoodOrderItem.quantity * FoodItem.price).label("total_revenue")
    ).join(
        FoodOrderItem, FoodOrderItem.food_item_id == FoodItem.id
    ).join(
        FoodOrder, FoodOrderItem.order_id == FoodOrder.id
    )
    
    if start_date:
        query = query.filter(func.date(FoodOrder.created_at) >= start_date)
    if end_date:
        query = query.filter(func.date(FoodOrder.created_at) <= end_date)
    
    query = query.group_by(FoodItem.id, FoodItem.name).order_by(
        func.sum(FoodOrderItem.quantity * FoodItem.price).desc()
    )
    
    results = query.offset(skip).limit(limit).all()
    
    return {
        "items": [
            {
                "item_name": r.name,
                "total_quantity": int(r.total_quantity or 0),
                "total_revenue": float(r.total_revenue or 0)
            }
            for r in results
        ],
        "total_items": len(results)
    }


@router.get("/restaurant/kot-analysis")
@apply_api_optimizations
def get_kot_analysis(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """KOT Analysis: Time between Order (KOT) and Service (Kitchen Efficiency)"""
    # Note: Requires order_time and service_time fields in FoodOrder
    # For now, using created_at as order_time
    query = db.query(FoodOrder).filter(FoodOrder.status == "completed")
    
    if start_date:
        query = query.filter(func.date(FoodOrder.created_at) >= start_date)
    if end_date:
        query = query.filter(func.date(FoodOrder.created_at) <= end_date)
    
    orders = query.options(
        joinedload(FoodOrder.room),
        joinedload(FoodOrder.items)
    ).offset(skip).limit(limit).all()
    
    result = []
    for order in orders:
        # Assuming service_time field exists - adjust based on actual model
        order_time = order.created_at
        service_time = getattr(order, 'service_time', None) or order.created_at
        
        if service_time and order_time:
            time_taken = (service_time - order_time).total_seconds() / 60  # minutes
        else:
            time_taken = 0
        
        result.append({
            "kot_number": f"KOT-{order.id}",
            "room_number": order.room.number if order.room else "Dine-in",
            "order_time": order_time.isoformat() if order_time else None,
            "service_time": service_time.isoformat() if service_time else None,
            "time_taken_minutes": round(time_taken, 2),
            "items_count": len(order.items),
            "status": order.status
        })
    
    return {"kot_analysis": result, "total": len(result)}


@router.get("/restaurant/void-cancellation")
@apply_api_optimizations
def get_void_cancellation_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Void / Cancellation Report: Tracks orders deleted after being punched (Security)"""
    # Note: Requires a deleted_at or voided_at field in FoodOrder
    # For now, checking status == "cancelled" or "voided"
    query = db.query(FoodOrder).filter(
        FoodOrder.status.in_(["cancelled", "voided"])
    )
    
    if start_date:
        query = query.filter(func.date(FoodOrder.created_at) >= start_date)
    if end_date:
        query = query.filter(func.date(FoodOrder.created_at) <= end_date)
    
    orders = query.options(
        joinedload(FoodOrder.room),
        joinedload(FoodOrder.employee),
        joinedload(FoodOrder.items)
    ).offset(skip).limit(limit).all()
    
    result = []
    for order in orders:
        result.append({
            "order_id": order.id,
            "room_number": order.room.number if order.room else "Dine-in",
            "order_time": order.created_at.isoformat() if order.created_at else None,
            "amount": order.amount,
            "status": order.status,
            "employee_name": order.employee.name if order.employee else "N/A",
            "items_count": len(order.items),
            "void_reason": getattr(order, 'void_reason', 'N/A')  # Add void_reason field
        })
    
    return {"voided_orders": result, "total": len(result)}


@router.get("/restaurant/discount-complimentary")
@apply_api_optimizations
def get_discount_complimentary_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Discount & Complimentary Report: Free meals given (Manager approval tracking)"""
    # Get orders with amount = 0 or discount > 0
    query = db.query(FoodOrder).filter(
        or_(
            FoodOrder.amount == 0,
            # Add discount_amount field check when available
        )
    )
    
    if start_date:
        query = query.filter(func.date(FoodOrder.created_at) >= start_date)
    if end_date:
        query = query.filter(func.date(FoodOrder.created_at) <= end_date)
    
    orders = query.options(
        joinedload(FoodOrder.room),
        joinedload(FoodOrder.employee),
        joinedload(FoodOrder.items)
    ).offset(skip).limit(limit).all()
    
    result = []
    for order in orders:
        result.append({
            "order_id": order.id,
            "room_number": order.room.number if order.room else "Dine-in",
            "order_time": order.created_at.isoformat() if order.created_at else None,
            "original_amount": getattr(order, 'original_amount', order.amount),
            "discount_amount": getattr(order, 'discount_amount', 0),
            "final_amount": order.amount,
            "approved_by": getattr(order, 'approved_by', 'N/A'),  # Add approved_by field
            "reason": getattr(order, 'complimentary_reason', 'N/A')  # Add reason field
        })
    
    return {"discounts_complimentary": result, "total": len(result)}


@router.get("/restaurant/nc-report")
@apply_api_optimizations
def get_nc_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """NC (Non-Chargeable) Report: Food given to Staff or Owners"""
    # Get orders marked as non-chargeable
    query = db.query(FoodOrder).filter(
        FoodOrder.billing_status == "non_chargeable"  # Add this status
    )
    
    if start_date:
        query = query.filter(func.date(FoodOrder.created_at) >= start_date)
    if end_date:
        query = query.filter(func.date(FoodOrder.created_at) <= end_date)
    
    orders = query.options(
        joinedload(FoodOrder.employee),
        joinedload(FoodOrder.items)
    ).offset(skip).limit(limit).all()
    
    result = []
    for order in orders:
        result.append({
            "order_id": order.id,
            "employee_name": order.employee.name if order.employee else "Owner/Staff",
            "order_time": order.created_at.isoformat() if order.created_at else None,
            "items": [
                {
                    "item_name": item.food_item.name if item.food_item else "N/A",
                    "quantity": item.quantity
                }
                for item in order.items
            ],
            "total_value": sum(
                (item.food_item.price or 0) * (item.quantity or 0)
                for item in order.items if item.food_item
            )
        })
    
    return {"nc_orders": result, "total": len(result)}


# ============================================
# 3. 📦 INVENTORY & PURCHASE REPORTS
# ============================================

@router.get("/inventory/stock-status")
@apply_api_optimizations
def get_stock_status_report(
    category_id: Optional[int] = Query(None),
    location: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Stock Status Report: Current quantity and value of every item"""
    query = db.query(InventoryItem).options(
        joinedload(InventoryItem.category),
        joinedload(InventoryItem.preferred_vendor)
    )
    
    if category_id:
        query = query.filter(InventoryItem.category_id == category_id)
    if location:
        query = query.filter(InventoryItem.location == location)
    
    items = query.offset(skip).limit(limit).all()
    
    result = []
    for item in items:
        stock_value = item.current_stock * item.unit_price
        result.append({
            "item_name": item.name,
            "item_code": item.item_code,
            "category": item.category.name if item.category else "N/A",
            "unit": item.unit,
            "current_stock": float(item.current_stock),
            "unit_price": float(item.unit_price),
            "stock_value": float(stock_value),
            "location": item.location,
            "min_stock_level": float(item.min_stock_level),
            "status": "Low Stock" if item.current_stock < item.min_stock_level else "OK"
        })
    
    return {"stock_status": result, "total": len(result)}


@router.get("/inventory/low-stock-alert")
@apply_api_optimizations
def get_low_stock_alert(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Low Stock Alert Report: Items below minimum level"""
    items = db.query(InventoryItem).filter(
        InventoryItem.current_stock < InventoryItem.min_stock_level
    ).options(
        joinedload(InventoryItem.category),
        joinedload(InventoryItem.preferred_vendor)
    ).all()
    
    result = []
    for item in items:
        shortage = item.min_stock_level - item.current_stock
        result.append({
            "item_name": item.name,
            "item_code": item.item_code,
            "category": item.category.name if item.category else "N/A",
            "current_stock": float(item.current_stock),
            "min_stock_level": float(item.min_stock_level),
            "shortage": float(shortage),
            "unit": item.unit,
            "preferred_vendor": item.preferred_vendor.name if item.preferred_vendor else "N/A",
            "urgency": "Critical" if item.current_stock == 0 else "High"
        })
    
    return {"low_stock_items": result, "total": len(result)}


@router.get("/inventory/expiry-aging")
@apply_api_optimizations
def get_expiry_aging_report(
    days_ahead: int = Query(3, ge=1, le=30, description="Days ahead to check for expiry"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Expiry / Aging Report: Perishable items expiring in next N days"""
    # Note: Requires expiry_date field in InventoryTransaction or InventoryItem
    # For now, checking perishable items
    cutoff_date = date.today() + timedelta(days=days_ahead)
    
    # Get perishable items with transactions
    items = db.query(InventoryItem).filter(
        InventoryItem.is_perishable == True
    ).options(
        joinedload(InventoryItem.category),
        joinedload(InventoryItem.transactions)
    ).all()
    
    result = []
    for item in items:
        # Check transactions for expiry dates
        for transaction in item.transactions:
            expiry_date = getattr(transaction, 'expiry_date', None)
            if expiry_date and expiry_date <= cutoff_date:
                days_until_expiry = (expiry_date - date.today()).days
                result.append({
                    "item_name": item.name,
                    "item_code": item.item_code,
                    "batch_number": getattr(transaction, 'batch_number', 'N/A'),
                    "quantity": float(transaction.quantity) if hasattr(transaction, 'quantity') else 0,
                    "expiry_date": expiry_date.isoformat() if expiry_date else None,
                    "days_until_expiry": days_until_expiry,
                    "location": item.location,
                    "urgency": "Expired" if days_until_expiry < 0 else ("Critical" if days_until_expiry <= 1 else "High")
                })
    
    return {"expiring_items": result, "total": len(result), "days_ahead": days_ahead}


@router.get("/inventory/stock-movement")
@apply_api_optimizations
def get_stock_movement_register(
    item_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Stock Movement Register: History of item (In -> Move -> Out)"""
    query = db.query(InventoryTransaction).options(
        joinedload(InventoryTransaction.item)
    )
    
    if item_id:
        query = query.filter(InventoryTransaction.item_id == item_id)
    if start_date:
        query = query.filter(func.date(InventoryTransaction.created_at) >= start_date)
    if end_date:
        query = query.filter(func.date(InventoryTransaction.created_at) <= end_date)
    
    transactions = query.order_by(InventoryTransaction.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for trans in transactions:
        result.append({
            "transaction_id": trans.id,
            "item_name": trans.item.name if trans.item else "N/A",
            "transaction_type": trans.transaction_type,  # purchase, consumption, transfer, etc.
            "quantity": float(trans.quantity),
            "unit": trans.item.unit if trans.item else "N/A",
            "from_location": getattr(trans, 'from_location', 'N/A'),
            "to_location": getattr(trans, 'to_location', 'N/A'),
            "reference": getattr(trans, 'reference', 'N/A'),  # Purchase ID, Requisition ID, etc.
            "created_at": trans.created_at.isoformat() if trans.created_at else None,
            "created_by": getattr(trans, 'created_by', 'N/A')
        })
    
    return {"stock_movements": result, "total": len(result)}


@router.get("/inventory/waste-spoilage")
@apply_api_optimizations
def get_waste_spoilage_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Waste & Spoilage Report: Value of items thrown away"""
    try:
        query = db.query(WasteLog).options(
            joinedload(WasteLog.item)
        )
        
        if start_date:
            query = query.filter(func.date(WasteLog.created_at) >= start_date)
        if end_date:
            query = query.filter(func.date(WasteLog.created_at) <= end_date)
        
        waste_logs = query.order_by(WasteLog.created_at.desc()).offset(skip).limit(limit).all()
        
        result = []
        total_waste_value = 0
        for waste in waste_logs:
            waste_value = waste.quantity * (waste.item.unit_price if waste.item else 0)
            total_waste_value += waste_value
            result.append({
                "item_name": waste.item.name if waste.item else "N/A",
                "quantity": float(waste.quantity),
                "unit": waste.item.unit if waste.item else "N/A",
                "waste_value": float(waste_value),
                "reason": waste.reason_code,
                "waste_date": waste.created_at.isoformat() if waste.created_at else None,
                "reported_by": getattr(waste, 'reported_by', 'N/A')
            })
        
        return {
            "waste_logs": result,
            "total_waste_value": float(total_waste_value),
            "total": len(result)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching waste/spoilage report: {str(e)}")


@router.get("/inventory/purchase-register")
@apply_api_optimizations
def get_purchase_register(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    vendor_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Purchase Register: List of all Vendor Bills entered"""
    try:
        query = db.query(PurchaseMaster).options(
            joinedload(PurchaseMaster.vendor),
            joinedload(PurchaseMaster.details).joinedload(PurchaseDetail.item)
        )
        
        if start_date:
            query = query.filter(PurchaseMaster.purchase_date >= start_date)
        if end_date:
            query = query.filter(PurchaseMaster.purchase_date <= end_date)
        if vendor_id:
            query = query.filter(PurchaseMaster.vendor_id == vendor_id)
        
        purchases = query.order_by(PurchaseMaster.purchase_date.desc()).offset(skip).limit(limit).all()
        
        result = []
        for purchase in purchases:
            result.append({
                "purchase_id": purchase.id,
                "invoice_number": purchase.invoice_number,
                "vendor_name": purchase.vendor.name if purchase.vendor else "N/A",
                "purchase_date": purchase.purchase_date.isoformat() if purchase.purchase_date else None,
                "total_amount": float(purchase.total_amount),
                "tax_amount": float(purchase.tax_amount),
                "payment_status": purchase.payment_status,
                "items_count": len(purchase.details)
            })
        
        return {"purchases": result, "total": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching purchase register: {str(e)}")


@router.get("/inventory/variance")
@apply_api_optimizations
def get_variance_report(
    location: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Variance Report: Difference between System Stock and Physical Audit Stock"""
    # Note: Requires physical_count field from audit
    # For now, returning items that may need audit
    query = db.query(InventoryItem).options(
        joinedload(InventoryItem.category)
    )
    
    if location:
        query = query.filter(InventoryItem.location == location)
    
    items = query.offset(skip).limit(limit).all()
    
    result = []
    for item in items:
        physical_count = getattr(item, 'physical_count', None)  # Add physical_count field
        system_stock = item.current_stock
        variance = (physical_count - system_stock) if physical_count is not None else 0
        variance_value = variance * item.unit_price
        
        result.append({
            "item_name": item.name,
            "item_code": item.item_code,
            "system_stock": float(system_stock),
            "physical_count": float(physical_count) if physical_count is not None else None,
            "variance": float(variance),
            "variance_value": float(variance_value),
            "unit": item.unit,
            "location": item.location,
            "status": "Match" if variance == 0 else ("Shortage" if variance < 0 else "Excess")
        })
    
    return {"variance_report": result, "total": len(result)}


# ============================================
# 4. 🧹 HOUSEKEEPING & FACILITY REPORTS
# ============================================

@router.get("/housekeeping/room-discrepancy")
@apply_api_optimizations
def get_room_discrepancy_report(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Room Discrepancy Report: Front Desk vs Housekeeping status mismatch"""
    # Get all rooms
    rooms = db.query(Room).all()
    
    result = []
    for room in rooms:
        # Check booking status
        booking = db.query(Booking).join(BookingRoom).filter(
            and_(
                BookingRoom.room_id == room.id,
                Booking.check_in <= date.today(),
                Booking.check_out > date.today(),
                Booking.status == "checked-in"
            )
        ).first()
        
        # Front desk status
        front_desk_status = "Occupied" if booking else "Vacant"
        
        # Housekeeping status (requires housekeeping_status field in Room)
        housekeeping_status = getattr(room, 'housekeeping_status', room.status)
        
        if front_desk_status != housekeeping_status:
            result.append({
                "room_number": room.number,
                "front_desk_status": front_desk_status,
                "housekeeping_status": housekeeping_status,
                "discrepancy": f"{front_desk_status} vs {housekeeping_status}",
                "guest_name": booking.guest_name if booking else "N/A",
                "severity": "Critical" if front_desk_status == "Vacant" and housekeeping_status == "Occupied" else "Warning"
            })
    
    return {"discrepancies": result, "total": len(result)}


@router.get("/housekeeping/laundry-cost")
@apply_api_optimizations
def get_laundry_cost_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Laundry Cost Report: Linen sent vs returned, torn/damaged tracking"""
    # Note: Requires laundry tracking in InventoryTransaction
    # Filter by items with track_laundry_cycle = True
    query = db.query(InventoryTransaction).join(InventoryItem).filter(
        InventoryItem.track_laundry_cycle == True
    )
    
    if start_date:
        query = query.filter(func.date(InventoryTransaction.created_at) >= start_date)
    if end_date:
        query = query.filter(func.date(InventoryTransaction.created_at) <= end_date)
    
    transactions = query.options(
        joinedload(InventoryTransaction.item)
    ).all()
    
    sent_count = 0
    returned_count = 0
    damaged_count = 0
    
    for trans in transactions:
        if trans.transaction_type == "laundry_sent":
            sent_count += trans.quantity
        elif trans.transaction_type == "laundry_returned":
            returned_count += trans.quantity
        elif trans.transaction_type == "laundry_damaged":
            damaged_count += trans.quantity
    
    return {
        "period": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        },
        "linen_sent": float(sent_count),
        "linen_returned": float(returned_count),
        "linen_damaged": float(damaged_count),
        "linen_pending": float(sent_count - returned_count - damaged_count)
    }


@router.get("/housekeeping/minibar-consumption")
@apply_api_optimizations
def get_minibar_consumption_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Minibar Consumption: Items consumed from room minibars"""
    # Get checkout verifications with consumables audit
    query = db.query(CheckoutVerification).join(Checkout).filter(
        CheckoutVerification.consumables_audit_data.isnot(None)
    )
    
    if start_date:
        query = query.filter(func.date(Checkout.checkout_date) >= start_date)
    if end_date:
        query = query.filter(func.date(Checkout.checkout_date) <= end_date)
    
    verifications = query.options(
        joinedload(CheckoutVerification.checkout)
    ).offset(skip).limit(limit).all()
    
    result = []
    for verification in verifications:
        consumables = verification.consumables_audit_data or {}
        for item_id, data in consumables.items():
            if isinstance(data, dict):
                actual = data.get('actual', 0)
                limit = data.get('limit', 0)
                charge = data.get('charge', 0)
                
                if actual > limit:
                    result.append({
                        "room_number": verification.room_number,
                        "checkout_date": verification.checkout.checkout_date.isoformat() if verification.checkout and verification.checkout.checkout_date else None,
                        "item_id": item_id,
                        "consumed": actual - limit,
                        "chargeable": charge > 0,
                        "charge_amount": float(charge)
                    })
    
    return {"minibar_consumption": result, "total": len(result)}


@router.get("/housekeeping/lost-found")
@apply_api_optimizations
def get_lost_found_register(
    status: Optional[str] = Query(None, description="Filter by status: found, claimed, disposed"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Lost & Found Register: Items left behind by guests"""
    # Note: Requires LostFound model - creating placeholder response
    # This would need a new model: LostFound(id, item_description, found_date, found_by, room_number, status, claimed_by, claimed_date)
    
    return {
        "message": "Lost & Found model not yet implemented",
        "lost_found_items": [],
        "total": 0
    }


@router.get("/housekeeping/maintenance-tickets")
@apply_api_optimizations
def get_maintenance_ticket_log(
    status: Optional[str] = Query(None, description="Filter by status: pending, in_progress, completed"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Maintenance Ticket Log: Status of repairs"""
    # Note: Requires MaintenanceTicket model - creating placeholder response
    # This would need a new model: MaintenanceTicket(id, room_number, issue_description, reported_date, status, assigned_to, completed_date)
    
    return {
        "message": "Maintenance Ticket model not yet implemented",
        "tickets": [],
        "total": 0
    }


@router.get("/housekeeping/asset-audit")
@apply_api_optimizations
def get_asset_audit_report(
    location: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Asset Audit Report: Fixed Assets mapped to locations vs actually found"""
    # Get fixed assets
    query = db.query(InventoryItem).filter(
        InventoryItem.is_asset_fixed == True
    ).options(
        joinedload(InventoryItem.category)
    )
    
    if location:
        query = query.filter(InventoryItem.location == location)
    
    assets = query.offset(skip).limit(limit).all()
    
    result = []
    for asset in assets:
        # Check AssetMapping for location
        mapped_location = getattr(asset, 'mapped_location', asset.location)
        actual_location = getattr(asset, 'actual_location', None)  # From audit
        
        result.append({
            "asset_name": asset.name,
            "asset_code": asset.item_code,
            "mapped_location": mapped_location,
            "actual_location": actual_location,
            "status": "Match" if mapped_location == actual_location else "Mismatch",
            "category": asset.category.name if asset.category else "N/A"
        })
    
    return {"asset_audit": result, "total": len(result)}


# ============================================
# 5. 💰 ACCOUNTS & GST REPORTS (Already exists in gst_reports.py)
# ============================================
# These are already implemented in app/api/gst_reports.py
# Just adding reference endpoints here


# ============================================
# 6. 🛡️ SECURITY & HR REPORTS
# ============================================

@router.get("/security/visitor-log")
@apply_api_optimizations
def get_visitor_log(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Visitor Log: Non-resident guests entering premises"""
    # Note: Requires VisitorLog model - creating placeholder response
    # This would need a new model: VisitorLog(id, visitor_name, purpose, time_in, time_out, room_visited, host_name)
    
    return {
        "message": "Visitor Log model not yet implemented",
        "visitors": [],
        "total": 0
    }


@router.get("/security/key-card-audit")
@apply_api_optimizations
def get_key_card_audit(
    room_number: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Key Card Audit: Who opened which room? (Staff Name + Timestamp)"""
    # Note: Requires KeyCardLog model - creating placeholder response
    # This would need a new model: KeyCardLog(id, room_number, staff_name, access_time, access_type, card_number)
    
    return {
        "message": "Key Card Audit model not yet implemented",
        "access_logs": [],
        "total": 0
    }


@router.get("/hr/staff-attendance")
@apply_api_optimizations
def get_staff_attendance_report(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    employee_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Staff Attendance: Shift In/Out times"""
    query = db.query(WorkingLog).options(
        joinedload(WorkingLog.employee)
    )
    
    if employee_id:
        query = query.filter(WorkingLog.employee_id == employee_id)
    if start_date:
        query = query.filter(WorkingLog.date >= start_date)
    if end_date:
        query = query.filter(WorkingLog.date <= end_date)
    
    logs = query.order_by(WorkingLog.date.desc()).offset(skip).limit(limit).all()
    
    result = []
    for log in logs:
        hours_worked = 0
        if log.check_in_time and log.check_out_time:
            # Calculate hours
            check_in = datetime.combine(log.date, log.check_in_time)
            check_out = datetime.combine(log.date, log.check_out_time)
            hours_worked = (check_out - check_in).total_seconds() / 3600
        
        result.append({
            "employee_name": log.employee.name if log.employee else "N/A",
            "employee_id": log.employee_id,
            "date": log.date.isoformat(),
            "check_in_time": log.check_in_time.isoformat() if log.check_in_time else None,
            "check_out_time": log.check_out_time.isoformat() if log.check_out_time else None,
            "hours_worked": round(hours_worked, 2),
            "location": log.location
        })
    
    return {"attendance_logs": result, "total": len(result)}


@router.get("/hr/payroll-register")
@apply_api_optimizations
def get_payroll_register(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Payroll Register: Salary calculation (Basic + OT - Deductions)"""
    if not year:
        year = date.today().year
    if not month:
        month = date.today().month
    
    # Get employees
    employees = db.query(Employee).offset(skip).limit(limit).all()
    
    result = []
    for employee in employees:
        # Get attendance for the month
        attendance_count = db.query(Attendance).filter(
            and_(
                Attendance.employee_id == employee.id,
                extract('month', Attendance.date) == month,
                extract('year', Attendance.date) == year,
                Attendance.status == "Present"
            )
        ).count()
        
        # Get working logs for OT calculation
        working_logs = db.query(WorkingLog).filter(
            and_(
                WorkingLog.employee_id == employee.id,
                extract('month', WorkingLog.date) == month,
                extract('year', WorkingLog.date) == year
            )
        ).all()
        
        total_hours = sum(
            (datetime.combine(log.date, log.check_out_time) - datetime.combine(log.date, log.check_in_time)).total_seconds() / 3600
            for log in working_logs
            if log.check_in_time and log.check_out_time
        )
        
        # Calculate salary components
        basic_salary = employee.salary or 0
        # Assuming 8 hours per day standard
        standard_hours = attendance_count * 8
        ot_hours = max(0, total_hours - standard_hours)
        ot_amount = (ot_hours * (basic_salary / (30 * 8))) * 1.5  # 1.5x for OT
        
        # Deductions (requires Leave model)
        leaves = db.query(Leave).filter(
            and_(
                Leave.employee_id == employee.id,
                extract('month', Leave.from_date) == month,
                extract('year', Leave.from_date) == year,
                Leave.status == "approved",
                Leave.leave_type == "Unpaid"
            )
        ).count()
        
        leave_deduction = (leaves * (basic_salary / 30))
        
        net_salary = basic_salary + ot_amount - leave_deduction
        
        result.append({
            "employee_name": employee.name,
            "employee_id": employee.id,
            "role": employee.role,
            "basic_salary": float(basic_salary),
            "attendance_days": attendance_count,
            "ot_hours": round(ot_hours, 2),
            "ot_amount": round(ot_amount, 2),
            "leave_deduction": float(leave_deduction),
            "net_salary": round(net_salary, 2),
            "month": month,
            "year": year
        })
    
    return {"payroll": result, "total": len(result)}


# ============================================
# 7. 📊 MANAGEMENT DASHBOARD
# ============================================

@router.get("/management/dashboard")
@apply_api_optimizations
def get_management_dashboard(
    report_date: Optional[date] = Query(None, description="Date for dashboard (default: today)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Management Dashboard: ADR, RevPAR, Food Cost %, Occupancy %"""
    if not report_date:
        report_date = date.today()
    
    # Total rooms
    total_rooms = db.query(Room).count()
    
    # Occupied rooms
    occupied_bookings = db.query(Booking).filter(
        and_(
            Booking.check_in <= report_date,
            Booking.check_out > report_date,
            Booking.status.in_(["checked-in", "booked"])
        )
    ).count()
    
    occupied_packages = db.query(PackageBooking).filter(
        and_(
            PackageBooking.check_in <= report_date,
            PackageBooking.check_out > report_date,
            PackageBooking.status.in_(["checked-in", "booked"])
        )
    ).count()
    
    occupied_rooms = occupied_bookings + occupied_packages
    occupancy_percentage = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0
    
    # Room revenue for the date
    room_revenue = db.query(func.sum(Checkout.room_total)).filter(
        func.date(Checkout.checkout_date) == report_date
    ).scalar() or 0
    
    # ADR (Average Daily Rate)
    checkouts_count = db.query(Checkout).filter(
        func.date(Checkout.checkout_date) == report_date
    ).count()
    
    adr = (room_revenue / checkouts_count) if checkouts_count > 0 else 0
    
    # RevPAR (Revenue Per Available Room)
    revpar = (room_revenue / total_rooms) if total_rooms > 0 else 0
    
    # Food revenue
    food_revenue = db.query(func.sum(Checkout.food_total)).filter(
        func.date(Checkout.checkout_date) == report_date
    ).scalar() or 0
    
    # Food cost (from inventory consumption)
    # This would require tracking food cost separately
    # For now, using a placeholder
    food_cost = 0  # Calculate from inventory consumption for food items
    
    food_cost_percentage = (food_cost / food_revenue * 100) if food_revenue > 0 else 0
    
    return {
        "date": report_date.isoformat(),
        "kpis": {
            "adr": round(float(adr), 2),
            "revpar": round(float(revpar), 2),
            "occupancy_percentage": round(occupancy_percentage, 2),
            "food_cost_percentage": round(food_cost_percentage, 2)
        },
        "details": {
            "total_rooms": total_rooms,
            "occupied_rooms": occupied_rooms,
            "room_revenue": float(room_revenue),
            "food_revenue": float(food_revenue),
            "checkouts_count": checkouts_count
        }
    }

