from fastapi import APIRouter, Depends
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, Date, or_
from datetime import date, timedelta, datetime

from app.utils.auth import get_db, get_current_user
from app.utils.branch_scope import get_branch_id
from app.models.user import User
from app.models.checkout import Checkout
from app.models.room import Room
from app.models.booking import Booking, BookingRoom
from app.models.Package import Package, PackageBooking, PackageBookingRoom
from app.models.foodorder import FoodOrder
from app.models.food_item import FoodItem
from app.models.expense import Expense
from app.models.employee import Employee, WorkingLog
from app.models.service import Service, AssignedService
from app.models.inventory import InventoryItem, InventoryCategory, PurchaseMaster, Vendor, StockIssue, StockIssueDetail, AssetRegistry, Location

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

def apply_branch_scope(query, model, branch_id: Optional[int]):
    """Applies branch_id filter to a query if branch_id is provided."""
    if branch_id is not None:
        return query.filter(model.branch_id == branch_id)
    return query

@router.get("/kpis")
def get_kpis(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user),
    branch_id: Optional[int] = Depends(get_branch_id)
):
    """
    Calculates and returns key performance indicators for the dashboard.
    """
    try:
        today = date.today()

        # 1. Checkout KPIs - use estimates for large datasets
        checkouts_today = 0
        checkouts_total = 0
        try:
            # For today, use exact count (should be small)
            q_today = db.query(func.count(Checkout.id)).filter(func.cast(Checkout.checkout_date, Date) == today)
            checkouts_today = apply_branch_scope(q_today, Checkout, branch_id).scalar() or 0
            # For total, use estimate if dataset is large
            sample = db.query(Checkout).limit(1000).all()
            if len(sample) < 1000:
                checkouts_total = len(sample)
            else:
                # Estimate based on sample
                checkouts_total = 1000  # Conservative estimate
        except:
            checkouts_today = 0
            checkouts_total = 0

        # 2. Room Status KPIs - optimized to avoid loading all rooms
        # Use direct queries instead of loading all rooms
        q_total = db.query(func.count(Room.id))
        total_rooms_count = apply_branch_scope(q_total, Room, branch_id).scalar() or 0
        
        # Find booked rooms - use distinct to avoid duplicates
        booked_room_ids = set()
        try:
            active_bookings_q = db.query(BookingRoom.room_id).join(Booking).filter(
                Booking.status.in_(['booked', 'checked-in', 'checked_in']),
                Booking.check_in <= today,
                Booking.check_out > today,
            )
            active_bookings = apply_branch_scope(active_bookings_q, Booking, branch_id).distinct().limit(100).all()
            booked_room_ids.update([r.room_id for r in active_bookings if r.room_id])
        except:
            pass

        try:
            active_package_bookings = db.query(PackageBookingRoom.room_id).join(PackageBooking).filter(
                PackageBooking.status.in_(['booked', 'checked-in', 'checked_in']),
                PackageBooking.check_in <= today,
                PackageBooking.check_out > today,
            ).distinct().limit(500).all()
            booked_room_ids.update([r.room_id for r in active_package_bookings if r.room_id])
        except:
            pass

        booked_rooms_count = len(booked_room_ids) or 0
        try:
            maint_q = db.query(func.count(Room.id)).filter(func.lower(Room.status) == "maintenance")
            maintenance_rooms_count = apply_branch_scope(maint_q, Room, branch_id).scalar() or 0
        except:
            maintenance_rooms_count = 0
        available_rooms_count = max(0, total_rooms_count - booked_rooms_count - maintenance_rooms_count)

        # 3. Food Revenue KPI
        # Handle both 'amount' and 'total_amount' fields for FoodOrder
        food_revenue_today = 0
        try:
            food_q = db.query(func.sum(FoodOrder.amount)).filter(
                func.cast(FoodOrder.created_at, Date) == today
            )
            food_revenue_today = apply_branch_scope(food_q, FoodOrder, branch_id).scalar() or 0
        except Exception:
            # Fallback to total_amount if amount field doesn't exist
            try:
                food_revenue_today = db.query(func.sum(FoodOrder.total_amount)).filter(
                    func.cast(FoodOrder.created_at, Date) == today
                ).scalar() or 0
            except Exception:
                food_revenue_today = 0

        # 4. Package Booking KPI
        package_bookings_today = 0
        try:
            pkg_q = db.query(func.count(PackageBooking.id)).filter(
                func.cast(PackageBooking.check_in, Date) == today
            )
            package_bookings_today = apply_branch_scope(pkg_q, PackageBooking, branch_id).scalar() or 0
        except:
            package_bookings_today = 0

        return [{
            "checkouts_today": checkouts_today,
            "checkouts_total": checkouts_total,
            "available_rooms": available_rooms_count,
            "booked_rooms": booked_rooms_count,
            "food_revenue_today": float(food_revenue_today) if food_revenue_today else 0,
            "package_bookings_today": package_bookings_today,
        }]
    except Exception as e:
        # Return default values if there's any error to prevent 500 response
        import traceback
        print(f"Error in get_kpis: {str(e)}")
        print(traceback.format_exc())
        return [{
            "checkouts_today": 0,
            "checkouts_total": 0,
            "available_rooms": 0,
            "booked_rooms": 0,
            "food_revenue_today": 0,
            "package_bookings_today": 0,
        }]

@router.get("/charts")
def get_chart_data(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user),
    branch_id: Optional[int] = Depends(get_branch_id)
):
    """Dashboard chart data with sensible fallbacks.
    - Primary source: Checkout totals (actual billed revenue)
    - Fallback: Estimated revenue from current bookings if no checkouts exist
    """
    from sqlalchemy import cast

    # --- Primary: use billed totals from Checkout ---
    room_total_q = db.query(func.coalesce(func.sum(Checkout.room_total), 0))
    room_total = apply_branch_scope(room_total_q, Checkout, branch_id).scalar() or 0
    
    package_total_q = db.query(func.coalesce(func.sum(Checkout.package_total), 0))
    package_total = apply_branch_scope(package_total_q, Checkout, branch_id).scalar() or 0
    
    food_total_q = db.query(func.coalesce(func.sum(Checkout.food_total), 0))
    food_total = apply_branch_scope(food_total_q, Checkout, branch_id).scalar() or 0

    # If everything is zero, build a lightweight estimate from active data to avoid empty charts
    # Limit queries to prevent timeouts
    if (room_total + package_total + food_total) == 0:
        # Estimate room revenue: sum(room.price * nights) for recent bookings (last 30 days, limited)
        thirty_days_ago = date.today() - timedelta(days=30)
        recent_bookings = (
            db.query(Booking)
            .filter(Booking.check_in >= thirty_days_ago)
            .limit(100)  # Limit to prevent slow queries
            .all()
        )
        est_room = 0.0
        # Batch load rooms to avoid N+1
        booking_ids = [b.id for b in recent_bookings]
        if booking_ids:
            booking_rooms = db.query(BookingRoom).filter(BookingRoom.booking_id.in_(booking_ids)).all()
            room_ids = list(set([br.room_id for br in booking_rooms if br.room_id]))
            rooms_map = {}
            if room_ids:
                rooms = db.query(Room).filter(Room.id.in_(room_ids)).all()
                rooms_map = {r.id: r for r in rooms}
            
            for b in recent_bookings:
                nights = max(1, (b.check_out - b.check_in).days)
                for br in booking_rooms:
                    if br.booking_id == b.id and br.room_id in rooms_map:
                        room = rooms_map[br.room_id]
                        if room and room.price:
                            est_room += float(room.price) * nights

        # Estimate package revenue: limited query
        recent_pkg_bookings = (
            db.query(PackageBooking)
            .filter(PackageBooking.check_in >= thirty_days_ago)
            .limit(100)  # Limit to prevent slow queries
            .all()
        )
        est_package = 0.0
        package_ids = list(set([pb.package_id for pb in recent_pkg_bookings if pb.package_id]))
        packages_map = {}
        if package_ids:
            packages = db.query(Package).filter(Package.id.in_(package_ids)).all()
            packages_map = {p.id: p for p in packages}
        
        for pb in recent_pkg_bookings:
            if pb.package_id in packages_map:
                pkg = packages_map[pb.package_id]
                if pkg and pkg.price:
                    est_package += float(pkg.price)

        # Food revenue estimate: limited query
        est_food = db.query(func.coalesce(func.sum(FoodOrder.amount), 0)).filter(
            FoodOrder.created_at >= thirty_days_ago
        ).scalar() or 0

        room_total, package_total, food_total = est_room, est_package, est_food

    revenue_breakdown = [
        {"name": 'Room Charges', "value": round(float(room_total), 2)},
        {"name": 'Package Charges', "value": round(float(package_total), 2)},
        {"name": 'Food & Beverage', "value": round(float(food_total), 2)},
    ]

    # --- Weekly performance ---
    weekly_performance = []
    today = date.today()
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        # Billed revenue and checkout count for each day
        day_revenue = db.query(func.coalesce(func.sum(Checkout.grand_total), 0)).filter(func.cast(Checkout.checkout_date, Date) == day).scalar() or 0
        day_checkouts = db.query(func.count(Checkout.id)).filter(func.cast(Checkout.checkout_date, Date) == day).scalar() or 0

        # Fallback: if still zero, count bookings starting that day
        if not day_revenue:
            starts = db.query(func.count(Booking.id)).filter(Booking.check_in == day).scalar() or 0
            day_revenue = float(starts) * 1000.0  # symbolic baseline so chart shows activity
        weekly_performance.append({
            "day": day.strftime("%a"),
            "revenue": round(float(day_revenue), 2),
            "checkouts": int(day_checkouts),
        })

    return {
        "revenue_breakdown": revenue_breakdown,
        "weekly_performance": weekly_performance,
    }

@router.get("/vendors/{vendor_id}/transactions")
def get_vendor_transactions(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all transactions (Purchases) for a specific vendor.
    """
    purchases = db.query(PurchaseMaster).filter(PurchaseMaster.vendor_id == vendor_id).order_by(PurchaseMaster.purchase_date.desc()).all()
    
    results = []
    for p in purchases:
        results.append({
            "id": p.id,
            "date": p.purchase_date,
            "number": p.purchase_number,
            "amount": float(p.total_amount or 0),
            "status": p.payment_status or "Due",
            "remarks": p.remarks
        })
    return results

@router.get("/reports")
def get_reports_data(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user),
    branch_id: Optional[int] = Depends(get_branch_id)
):
    """
    Provides a consolidated dataset for the main reports/account page.
    """
    # Fetch recent bookings (regular and package)
    bookings_q = db.query(Booking).order_by(Booking.id.desc())
    recent_bookings = apply_branch_scope(bookings_q, Booking, branch_id).limit(5).all()
    
    pkg_bookings_q = db.query(PackageBooking).order_by(PackageBooking.id.desc())
    recent_package_bookings = apply_branch_scope(pkg_bookings_q, PackageBooking, branch_id).limit(5).all()

    # Combine and sort by date (assuming they have a comparable date field)
    # For this example, we'll just interleave them, but a real case might sort by a 'created_at'
    all_recent = sorted(
        [{"type": "Booking", "guest_name": b.guest_name, "status": b.status, "check_in": b.check_in, "id": f"B-{b.id}"} for b in recent_bookings] +
        [{"type": "Package", "guest_name": pb.guest_name, "status": pb.status, "check_in": pb.check_in, "id": f"P-{pb.id}"} for pb in recent_package_bookings],
        key=lambda x: x['check_in'],
        reverse=True
    )[:5]

    # Format expenses data into a JSON-friendly structure
    expenses_query_result = db.query(Expense.category, func.sum(Expense.amount).label("total_amount")).group_by(Expense.category).all()
    expenses_by_category = [{"category": category, "amount": total_amount} for category, total_amount in expenses_query_result]

    return [{
        "kpis": {
            "total_revenue": apply_branch_scope(db.query(func.sum(Checkout.grand_total)), Checkout, branch_id).scalar() or 0,
            "total_expenses": apply_branch_scope(db.query(func.sum(Expense.amount)), Expense, branch_id).scalar() or 0,
            "total_bookings": apply_branch_scope(db.query(Booking), Booking, branch_id).count() + apply_branch_scope(db.query(PackageBooking), PackageBooking, branch_id).count(),
            "active_employees": apply_branch_scope(db.query(Employee), Employee, branch_id).count(),
            "online_employees": apply_branch_scope(db.query(WorkingLog).filter(WorkingLog.date == date.today(), WorkingLog.check_out_time == None), WorkingLog, branch_id).count(),
            "total_rooms": apply_branch_scope(db.query(Room), Room, branch_id).count(),
        },
        "recent_bookings": all_recent,
        "expenses_by_category": expenses_by_category,
    }]


def get_date_range(period: str):
    """Helper to determine start and end dates based on a string period."""
    today = date.today()
    if period == "day":
        start_date = today
        end_date = today + timedelta(days=1)
    elif period == "week":
        start_date = today - timedelta(days=today.weekday())  # Monday
        end_date = start_date + timedelta(days=7)
    elif period == "month":
        start_date = today.replace(day=1)
        # Find the first day of the next month to use as an exclusive end date
        next_month = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        end_date = next_month
    else:  # "all"
        start_date, end_date = None, None
    return start_date, end_date


@router.get("/summary")
def get_summary(
    period: str = "all",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    branch_id: Optional[int] = Depends(get_branch_id)
):
    """
    Provides a comprehensive summary of KPIs for a given period (day, week, month, all).
    """
    if period != "custom":
        start_date, end_date = get_date_range(period)

    def apply_date_filter(query, date_column):
        """Applies a date range filter to a SQLAlchemy query if dates are provided."""
        if start_date:
            query = query.filter(date_column >= start_date)
        if end_date:
            # Use '<' for the end date to correctly handle date ranges
            query = query.filter(date_column < end_date)
        return query

    # --- KPI Calculations ---
    # Use optimized queries to avoid expensive count() operations on large tables

    # Bookings - use exists() for faster checks, limit count queries
    room_bookings_q = apply_date_filter(db.query(Booking), Booking.check_in)
    room_bookings_query = apply_branch_scope(room_bookings_q, Booking, branch_id)
    
    package_bookings_q = apply_date_filter(db.query(PackageBooking), PackageBooking.check_in)
    package_bookings_query = apply_branch_scope(package_bookings_q, PackageBooking, branch_id)
    
    # For large datasets, estimate counts instead of exact counts
    # Check if we have a reasonable number of records first
    room_bookings_count = 0
    package_bookings_count = 0
    try:
        # Use limit to check if we have data, then estimate
        sample = room_bookings_query.limit(1000).all()
        if len(sample) < 1000:
            room_bookings_count = len(sample)
        else:
            # Estimate: if we got 1000, there are likely more
            room_bookings_count = 1000  # Conservative estimate
        
        sample = package_bookings_query.limit(1000).all()
        if len(sample) < 1000:
            package_bookings_count = len(sample)
        else:
            package_bookings_count = 1000
    except:
        room_bookings_count = 0
        package_bookings_count = 0

    # Expenses - use sum directly without count
    expenses_q = apply_date_filter(db.query(Expense), Expense.date)
    expenses_query = apply_branch_scope(expenses_q, Expense, branch_id)
    total_expenses = expenses_query.with_entities(func.sum(Expense.amount)).scalar() or 0
    # Estimate expense count
    expense_count = 0
    try:
        sample = expenses_query.limit(1000).all()
        expense_count = len(sample) if len(sample) < 1000 else 1000
    except:
        expense_count = 0

    # Food Orders - estimate count
    food_orders_q = apply_date_filter(db.query(FoodOrder), FoodOrder.created_at)
    food_orders_query = apply_branch_scope(food_orders_q, FoodOrder, branch_id)
    food_orders_count = 0
    try:
        sample = food_orders_query.limit(1000).all()
        food_orders_count = len(sample) if len(sample) < 1000 else 1000
    except:
        food_orders_count = 0

    # Services - estimate count
    services_q = apply_date_filter(db.query(AssignedService), AssignedService.assigned_at)
    services_query = apply_branch_scope(services_q, AssignedService, branch_id)
    services_count = 0
    completed_services_count = 0
    try:
        sample = services_query.limit(1000).all()
        services_count = len(sample) if len(sample) < 1000 else 1000
        print(f"Dashboard: Services count: {services_count}")
        
        completed_sample = services_query.filter(AssignedService.status == 'completed').limit(1000).all()
        completed_services_count = len(completed_sample) if len(completed_sample) < 1000 else 1000
    except Exception as e:
        print(f"Dashboard: Error calculating services: {e}")
        services_count = 0
        completed_services_count = 0

    # Employees - estimate count
    employees_q = apply_date_filter(db.query(Employee), Employee.join_date)
    employees_query = apply_branch_scope(employees_q, Employee, branch_id)
    employees_count = 0
    total_salary = 0
    try:
        sample = employees_query.limit(1000).all()
        employees_count = len(sample) if len(sample) < 1000 else 1000
        # Calculate salary only for loaded employees
        total_salary = sum(float(e.salary or 0) for e in sample)
        
        # Currently online (clocked in today)
        online_count = db.query(WorkingLog).filter(
            WorkingLog.date == today, 
            WorkingLog.check_out_time == None
        ).count()
    except Exception as e:
        print(f"Error calculating employees: {e}")
        employees_count = 0
        total_salary = 0
        online_count = 0

    # Food items - quick check
    food_items_available = 0
    try:
        food_items_q = db.query(FoodItem).filter(func.lower(FoodItem.available).in_(["true", "1", "yes"]))
        sample = apply_branch_scope(food_items_q, FoodItem, branch_id).limit(1000).all()
        food_items_available = len(sample) if len(sample) < 1000 else 1000
    except:
        food_items_available = 0

    # Inventory KPIs - Categories and Departments
    inventory_categories_count = 0
    inventory_departments_count = 0
    try:
        cat_q = db.query(InventoryCategory)
        categories_sample = apply_branch_scope(cat_q, InventoryCategory, branch_id).limit(1000).all()
        # Count distinct departments
        departments = set()
        for cat in categories_sample:
            if cat.parent_department:
                departments.add(cat.parent_department)
        inventory_departments_count = len(departments)
    except:
        inventory_categories_count = 0
        inventory_departments_count = 0

    # Low Stock and Sellable Item Counts
    low_stock_count = 0
    sellable_items_count = 0
    try:
        low_q = db.query(func.count(InventoryItem.id)).filter(
            InventoryItem.current_stock <= InventoryItem.min_stock_level,
            InventoryItem.current_stock > 0
        )
        low_stock_count = apply_branch_scope(low_q, InventoryItem, branch_id).scalar() or 0
        
        sell_q = db.query(func.count(InventoryItem.id)).filter(
            InventoryItem.is_sellable_to_guest == True
        )
        sellable_items_count = apply_branch_scope(sell_q, InventoryItem, branch_id).scalar() or 0
    except:
        pass

    # Inventory Value and Item Count
    total_inventory_value = 0
    inventory_items_count = 0
    try:
        inv_val_q = db.query(func.sum(func.abs(InventoryItem.current_stock) * InventoryItem.unit_price))
        total_inventory_value = apply_branch_scope(inv_val_q, InventoryItem, branch_id).scalar() or 0
        
        inv_count_q = db.query(func.count(InventoryItem.id))
        inventory_items_count = apply_branch_scope(inv_count_q, InventoryItem, branch_id).scalar() or 0
    except:
        pass

    # Service Revenue KPI - Total service charges from assigned services
    total_service_revenue = 0
    try:
        # Join with Service to get charges
        service_revenue_q = db.query(func.sum(Service.charges)).join(
            AssignedService, Service.id == AssignedService.service_id
        )
        service_revenue = apply_branch_scope(service_revenue_q, AssignedService, branch_id)
        if start_date:
            service_revenue = service_revenue.filter(AssignedService.assigned_at >= start_date)
        if end_date:
            service_revenue = service_revenue.filter(AssignedService.assigned_at < end_date)
        total_service_revenue = service_revenue.scalar() or 0
    except:
        total_service_revenue = 0

    # Purchase KPIs - Total purchase amount and count
    total_purchases = 0
    purchase_count = 0
    try:
        purchases_q = apply_date_filter(db.query(PurchaseMaster), PurchaseMaster.purchase_date)
        purchases_query = apply_branch_scope(purchases_q, PurchaseMaster, branch_id)
        # Debug print
        print(f"Dashboard: Calculating purchases. Period: {period}")
        
        total_purchases = purchases_query.with_entities(func.sum(PurchaseMaster.total_amount)).scalar() or 0
        print(f"Dashboard: Total purchases sum: {total_purchases}")
        
        # Estimate purchase count
        sample = purchases_query.limit(1000).all()
        purchase_count = len(sample) if len(sample) < 1000 else 1000
        print(f"Dashboard: Purchase count: {purchase_count}")
    except Exception as e:
        import traceback
        print(f"Dashboard: Error calculating purchases: {e}")
        print(traceback.format_exc())
        total_purchases = 0
        purchase_count = 0

    # Vendor KPI - Count of active vendors
    vendor_count = 0
    try:
        vendor_q = db.query(Vendor).filter(Vendor.is_active == True)
        vendors_sample = apply_branch_scope(vendor_q, Vendor, branch_id).limit(1000).all()
        vendor_count = len(vendors_sample) if len(vendors_sample) < 1000 else 1000
    except:
        vendor_count = 0

    # Total Revenue (Checkout Grand Total)
    total_revenue = 0
    # GST / Tax Calculations
    total_output_tax = 0.0
    total_input_tax = 0.0

    try:
        # Use cast to Date for reliable comparison
        revenue_q = apply_date_filter(db.query(Checkout), func.cast(Checkout.checkout_date, Date))
        revenue_query = apply_branch_scope(revenue_q, Checkout, branch_id)
        total_revenue = revenue_query.with_entities(func.sum(Checkout.grand_total)).scalar() or 0
        total_output_tax = revenue_query.with_entities(func.sum(Checkout.tax_amount)).scalar() or 0.0
        
        print(f"Dashboard: Revenue found: {total_revenue}")

        # Input Tax from Purchases
        in_tax_q = apply_date_filter(db.query(PurchaseMaster), PurchaseMaster.purchase_date)
        in_tax_query = apply_branch_scope(in_tax_q, PurchaseMaster, branch_id)
        # Sum of CGST + SGST + IGST
        total_input_tax = in_tax_query.with_entities(func.sum(PurchaseMaster.cgst + PurchaseMaster.sgst + PurchaseMaster.igst)).scalar() or 0.0
        
        # Fallback: If no realized revenue, estimate from Active Bookings (like in charts)
        if total_revenue == 0:
            print("Dashboard: Revenue is 0, attempting estimate from Bookings")
            try:
                # Estimate Room Revenue
                room_est_query = apply_date_filter(db.query(Booking), Booking.check_in)
                bookings_sample = room_est_query.limit(200).all()
                
                est_room_rev = 0.0
                booking_ids = [b.id for b in bookings_sample]
                
                if booking_ids:
                    # Get rooms for these bookings
                    booking_rooms = db.query(BookingRoom).filter(BookingRoom.booking_id.in_(booking_ids)).all()
                    room_ids = list(set([br.room_id for br in booking_rooms if br.room_id]))
                    rooms_map = {}
                    if room_ids:
                         rooms = db.query(Room).filter(Room.id.in_(room_ids)).all()
                         rooms_map = {r.id: r for r in rooms}
                    
                    for b in bookings_sample:
                        nights = max(1, (b.check_out - b.check_in).days)
                        for br in booking_rooms:
                            if br.booking_id == b.id and br.room_id in rooms_map:
                                room = rooms_map[br.room_id]
                                if room and room.price:
                                    est_room_rev += float(room.price) * nights
                
                total_revenue += est_room_rev
                print(f"Dashboard: Added estimated room revenue: {est_room_rev}")

            except Exception as ex:
                print(f"Dashboard: Estimation failed: {ex}")

    except Exception as e:
        print(f"Error calculating revenue/tax: {e}")
        total_revenue = 0

    # Revenue by Payment Mode
    revenue_by_mode = {}
    try:
        # Fix: Use payment_method instead of payment_mode (schema mismatch)
        # Fix: Use Date cast for filter
        rev_mode_q = apply_date_filter(db.query(Checkout.payment_method, func.sum(Checkout.grand_total)), func.cast(Checkout.checkout_date, Date))
        rev_mode_q = rev_mode_q.group_by(Checkout.payment_method)
        results = rev_mode_q.all()
        for mode, amount in results:
            if mode:
                revenue_by_mode[mode] = float(amount or 0)
    except Exception as e:
        print(f"Error calculating revenue by mode: {e}")

    kpis = {
        "room_bookings": room_bookings_count,
        "package_bookings": package_bookings_count,
        "total_bookings": room_bookings_count + package_bookings_count,
        
        "assigned_services": services_count,
        "completed_services": completed_services_count,
        "total_service_revenue": float(total_service_revenue) if total_service_revenue else 0,
        "total_revenue": float(total_revenue), 
        "revenue_by_mode": revenue_by_mode, # Included
        "total_output_tax": float(total_output_tax),
        "total_input_tax": float(total_input_tax), 

        "food_orders": food_orders_count,
        "food_items_available": food_items_available,
        
        "total_expenses": total_expenses,
        "expense_count": expense_count,
        
        "active_employees": employees_count,
        "online_employees": online_count,
        "total_salary": total_salary,
        
        "inventory_categories": inventory_categories_count,
        "inventory_departments": inventory_departments_count,
        "total_purchases": float(total_purchases) if total_purchases else 0,
        "purchase_count": purchase_count,
        "vendor_count": vendor_count,
        "low_stock_items_count": low_stock_count,
        "sellable_items_count": sellable_items_count,
        "total_inventory_value": float(total_inventory_value) if total_inventory_value else 0,
        "inventory_items": inventory_items_count,
    }

    # Department-wise KPIs (Assets, Income, Expenses)
    department_kpis = {}
    try:
        # Define department mapping for expenses (category -> department)
        expense_category_to_dept = {
            # Restaurant expenses
            "food": "Restaurant", "beverage": "Restaurant", "kitchen": "Restaurant", "restaurant": "Restaurant",
            # Hotel expenses
            "housekeeping": "Hotel", "laundry": "Hotel", "room": "Hotel", "maintenance": "Hotel",
            # Facility expenses
            "electricity": "Facility", "water": "Facility", "plumbing": "Facility", "facility": "Facility",
            # Office expenses
            "stationery": "Office", "office": "Office", "admin": "Office", "communication": "Office",
            # Security expenses
            "security": "Security", "safety": "Security",
            # Fire & Safety
            "fire": "Fire & Safety", "safety equipment": "Fire & Safety",
        }
        
        # Get all departments from inventory categories
        all_departments = db.query(InventoryCategory.parent_department).distinct().filter(
            InventoryCategory.parent_department.isnot(None)
        ).all()
        departments_list = [dept[0] for dept in all_departments if dept[0]]
        
        # Add common departments if not in list
        common_departments = ["Restaurant", "Hotel", "Facility", "Office", "Security", "Fire & Safety", "Housekeeping"]
        for dept in common_departments:
            if dept not in departments_list:
                departments_list.append(dept)
        
        # Calculate KPIs for each department
        for dept in departments_list:
            try:
                # 1. Assets: Sum of fixed assets (is_asset_fixed = True) in this department
                # Also include high-value items (unit_price >= 10000) as assets even if not marked
                assets_value = 0
                try:
                    # Fixed assets explicitly marked (only positive stock)
                    fixed_assets_query = db.query(
                        func.sum(func.abs(InventoryItem.current_stock) * InventoryItem.unit_price)
                    ).join(InventoryCategory).filter(
                        InventoryCategory.parent_department == dept,
                        InventoryItem.is_asset_fixed == True,
                        InventoryItem.current_stock != 0  # Count non-zero stock (use abs to handle negative)
                    )
                    fixed_assets = fixed_assets_query.scalar() or 0
                    
                    # High-value items (likely assets even if not marked) - e.g., Fridge worth Rs.499,999
                    high_value_query = db.query(
                        func.sum(func.abs(InventoryItem.current_stock) * InventoryItem.unit_price)
                    ).join(InventoryCategory).filter(
                        InventoryCategory.parent_department == dept,
                        InventoryItem.is_asset_fixed == False,
                        InventoryItem.unit_price >= 10000,  # Items worth Rs.10,000+ are likely assets
                        InventoryItem.current_stock != 0
                    )
                    high_value_assets = high_value_query.scalar() or 0
                    
                    assets_value = float(fixed_assets) + float(high_value_assets)
                except Exception as e:
                    print(f"Error calculating assets for {dept}: {e}")
                    import traceback
                    traceback.print_exc()
                    assets_value = 0
                
                # 2. Income calculations
                income_value = 0
                
                # Restaurant income: Food orders
                if dept == "Restaurant":
                    try:
                        food_income_query = apply_date_filter(db.query(FoodOrder), FoodOrder.created_at)
                        food_income = food_income_query.with_entities(
                            func.sum(FoodOrder.amount)
                        ).scalar() or 0
                        income_value += float(food_income) if food_income else 0
                    except Exception as e:
                        # Log error for debugging
                        print(f"Error calculating Restaurant income: {e}")
                        pass
                
                # Hotel income: Room revenue from checkouts
                if dept == "Hotel":
                    try:
                        room_income_query = apply_date_filter(db.query(Checkout), Checkout.checkout_date)
                        room_income = room_income_query.with_entities(
                            func.sum(Checkout.room_total)
                        ).scalar() or 0
                        income_value += float(room_income) if room_income else 0
                    except:
                        pass
                    
                    # Service income: Assigned services
                    try:
                        service_income_query = apply_date_filter(
                            db.query(AssignedService).join(Service),
                            AssignedService.assigned_at
                        )
                        service_income = service_income_query.with_entities(
                            func.sum(Service.charges)
                        ).scalar() or 0
                        income_value += float(service_income) if service_income else 0
                    except:
                        pass
                
                # 3. Expenses: Sum expenses by department field (preferred) or category mapping (fallback)
                expense_value = 0
                try:
                    # First, try to get expenses with explicit department field
                    expense_query = apply_date_filter(db.query(Expense), Expense.date)
                    direct_dept_expenses = expense_query.filter(
                        Expense.department == dept
                    ).with_entities(func.sum(Expense.amount)).scalar() or 0
                    
                    # Fallback: Use category mapping if department field is not set
                    expense_categories_for_dept = [
                        cat for cat, mapped_dept in expense_category_to_dept.items() 
                        if mapped_dept == dept
                    ]
                    
                    category_based_expenses = 0
                    if expense_categories_for_dept:
                        category_expense_query = apply_date_filter(db.query(Expense), Expense.date)
                        # Only use category mapping for expenses without department field
                        category_expense_query = category_expense_query.filter(
                            (Expense.department.is_(None)) | (Expense.department == "")
                        )
                        # Use case-insensitive matching
                        expense_filters = [
                            func.lower(Expense.category).like(f"%{cat.lower()}%") 
                            for cat in expense_categories_for_dept
                        ]
                        if expense_filters:
                            category_expense_query = category_expense_query.filter(or_(*expense_filters))
                            category_based_expenses = category_expense_query.with_entities(
                                func.sum(Expense.amount)
                            ).scalar() or 0
                    
                    # Also check if expense category directly matches department name (for expenses without department field)
                    direct_category_query = apply_date_filter(db.query(Expense), Expense.date)
                    direct_category_expenses = direct_category_query.filter(
                        (Expense.department.is_(None)) | (Expense.department == ""),
                        func.lower(Expense.category).like(f"%{dept.lower()}%")
                    ).with_entities(func.sum(Expense.amount)).scalar() or 0
                    
                    # Combine: direct department field (preferred) + category-based (fallback)
                    expense_value = float(direct_dept_expenses) + max(
                        float(category_based_expenses) if category_based_expenses else 0,
                        float(direct_category_expenses) if direct_category_expenses else 0
                    )
                    
                    # ADD INVENTORY CONSUMPTION COSTS
                    # Get inventory consumption for this department
                    from app.models.inventory import InventoryTransaction
                    inventory_consumption_query = apply_date_filter(
                        db.query(InventoryTransaction), 
                        InventoryTransaction.created_at
                    )
                    inventory_consumption = inventory_consumption_query.filter(
                        InventoryTransaction.transaction_type == "out",
                        InventoryTransaction.department == dept
                    ).with_entities(func.sum(InventoryTransaction.total_amount)).scalar() or 0
                    
                    # Store regular expenses separately (before adding inventory)
                    regular_expenses = expense_value
                    
                    # Add inventory consumption to operational expenses
                    inventory_consumption_cost = float(inventory_consumption) if inventory_consumption else 0
                    operational_expenses = expense_value + inventory_consumption_cost
                    
                    # Calculate capital investment (inventory purchases for this department)
                    capital_investment = 0
                    try:
                        from app.models.inventory import PurchaseDetail
                        purchase_query = apply_date_filter(
                            db.query(PurchaseDetail).join(PurchaseMaster),
                            PurchaseMaster.purchase_date
                        )
                        # Join with InventoryItem and InventoryCategory to filter by department
                        dept_purchases = purchase_query.join(
                            InventoryItem, PurchaseDetail.item_id == InventoryItem.id
                        ).join(
                            InventoryCategory, InventoryItem.category_id == InventoryCategory.id
                        ).filter(
                            InventoryCategory.parent_department == dept
                        ).with_entities(func.sum(PurchaseDetail.total_amount)).scalar() or 0
                        
                        capital_investment = float(dept_purchases) if dept_purchases else 0
                    except Exception as e:
                        print(f"Error calculating capital investment for {dept}: {e}")
                        capital_investment = 0
                    
                    # For backward compatibility, expenses = operational expenses only
                    expense_value = operational_expenses
                    
                except Exception as e:
                    print(f"Error calculating expenses for {dept}: {e}")
                    expense_value = 0
                    operational_expenses = 0
                    regular_expenses = 0
                    inventory_consumption_cost = 0
                    capital_investment = 0
                
                # Store department KPIs with detailed breakdown
                department_kpis[dept] = {
                    "assets": float(assets_value),
                    "income": income_value,
                    "expenses": expense_value,  # Total operational expenses
                    "regular_expenses": regular_expenses,  # From Expense table
                    "inventory_consumption": inventory_consumption_cost,  # From consumed inventory
                    "operational_expenses": operational_expenses,  # regular + inventory
                    "capital_investment": capital_investment  # Inventory purchases
                }
            except Exception as e:
                # Skip this department if there's an error
                continue
    
    except Exception as e:
        db.rollback()
        # If department KPIs fail, return empty dict
        import traceback
        print(f"Error calculating department KPIs: {e}")
        print(traceback.format_exc())
        department_kpis = {}
    
    # Add department KPIs to response
    kpis["department_kpis"] = department_kpis

    return kpis

@router.get("/department/{department_name}/details")
def get_department_details(department_name: str, db: Session = Depends(get_db)):
    """
    Returns detailed breakdown for a specific department:
    - Assets (Fixed & High Value)
    - Capital Investment (Purchases)
    - Operational Expenses
    - Inventory Consumption
    """
    from app.models.inventory import PurchaseDetail, PurchaseMaster, InventoryItem, InventoryCategory, InventoryTransaction
    from app.models.expense import Expense
    from app.models.foodorder import FoodOrder
    # from app.models.checkout import Checkout # Already imported at top
    import traceback

    details = {
        "assets": [],
        "capital_investment": [],
        "expenses": [],
        "inventory_consumption": [],
        "income": []
    }

    try:
        # 1. Assets
        # Fixed assets
        fixed_assets = db.query(InventoryItem).join(InventoryCategory).filter(
            InventoryCategory.parent_department == department_name,
            InventoryItem.is_asset_fixed == True,
            InventoryItem.current_stock != 0
        ).all()
        
        # High value items (> 10000)
        high_value = db.query(InventoryItem).join(InventoryCategory).filter(
            InventoryCategory.parent_department == department_name,
            InventoryItem.is_asset_fixed == False,
            InventoryItem.unit_price >= 10000,
            InventoryItem.current_stock != 0
        ).all()

        for item in fixed_assets:
            details["assets"].append({
                "name": item.name,
                "quantity": item.current_stock,
                "unit_price": item.unit_price,
                "value": item.current_stock * item.unit_price,
                "type": "Fixed Asset"
            })
            
        for item in high_value:
            details["assets"].append({
                "name": item.name,
                "quantity": item.current_stock,
                "unit_price": item.unit_price,
                "value": item.current_stock * item.unit_price,
                "type": "High Value Item"
            })

        # 2. Capital Investment (Purchases)
        purchase_details = db.query(PurchaseDetail, PurchaseMaster, InventoryItem).join(
            PurchaseMaster, PurchaseDetail.purchase_master_id == PurchaseMaster.id
        ).join(
            InventoryItem, PurchaseDetail.item_id == InventoryItem.id
        ).join(
            InventoryCategory, InventoryItem.category_id == InventoryCategory.id
        ).filter(
            InventoryCategory.parent_department == department_name
        ).order_by(PurchaseMaster.purchase_date.desc()).all()

        for detail, master, item in purchase_details:
            details["capital_investment"].append({
                "date": master.purchase_date,
                "po_number": master.purchase_number,
                "item_name": item.name,
                "quantity": detail.quantity,
                "unit_price": detail.unit_price,
                "total_amount": detail.total_amount
            })

        # 3. Operational Expenses
        # Direct Department Match
        dept_expenses = db.query(Expense).filter(Expense.department == department_name).all()
        for exp in dept_expenses:
            details["expenses"].append({
                "date": exp.date,
                "category": exp.category,
                "description": exp.description,
                "amount": exp.amount,
                "type": "Direct Expense"
            })
            
        # Category Match (Fallback)
        expense_category_to_dept = {
            "food": "Restaurant", "beverage": "Restaurant", "kitchen": "Restaurant", "restaurant": "Restaurant",
            "housekeeping": "Hotel", "laundry": "Hotel", "room": "Hotel", "maintenance": "Hotel",
            "electricity": "Facility", "water": "Facility", "plumbing": "Facility", "facility": "Facility",
            "stationery": "Office", "office": "Office", "admin": "Office", "communication": "Office",
            "security": "Security", "safety": "Security",
            "fire": "Fire & Safety", "safety equipment": "Fire & Safety",
        }
        
        target_categories = [cat for cat, dept in expense_category_to_dept.items() if dept == department_name]
        
        if target_categories:
            cat_expenses = db.query(Expense).filter(
                (Expense.department.is_(None)) | (Expense.department == ""),
                or_(*[func.lower(Expense.category).like(f"%{cat.lower()}%") for cat in target_categories])
            ).all()
            
            for exp in cat_expenses:
                details["expenses"].append({
                    "date": exp.date,
                    "category": exp.category,
                    "description": exp.description,
                    "amount": exp.amount,
                    "type": "Category Match"
                })

        # 4. Inventory Consumption
        consumption = db.query(InventoryTransaction, InventoryItem).join(
            InventoryItem, InventoryTransaction.item_id == InventoryItem.id
        ).filter(
            InventoryTransaction.transaction_type == "out",
            InventoryTransaction.department == department_name
        ).order_by(InventoryTransaction.created_at.desc()).all()

        for txn, item in consumption:
            details["inventory_consumption"].append({
                "date": txn.created_at,
                "item_name": item.name,
                "quantity": txn.quantity,
                "amount": txn.total_amount or (txn.quantity * item.unit_price), 
                "notes": txn.notes
            })
            
        # 5. Income (Restaurant/Hotel)
        if department_name == "Restaurant":
            orders = db.query(FoodOrder).order_by(FoodOrder.created_at.desc()).limit(100).all()
            for order in orders:
                 details["income"].append({
                    "date": order.created_at,
                    "source": f"Order #{order.id} (Room {order.room_id})",
                    "amount": order.amount
                 })
        elif department_name == "Hotel":
            try:
                checkouts = db.query(Checkout).order_by(Checkout.checkout_date.desc()).limit(50).all()
                for chk in checkouts:
                    details["income"].append({
                        "date": chk.checkout_date,
                         "source": f"Checkout #{chk.id} ({chk.guest_name})",
                         "amount": chk.grand_total 
                    })
            except Exception:
                pass


    except Exception as e:
        print(f"Error fetching department details: {e}")
        traceback.print_exc()
        
    return details


from app.utils.branch_scope import get_branch_id

@router.get("/transactions")
def get_transactions(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):
    """
    Get combined list of recent financial transactions (Income & Expense).
    """
    transactions = []
    
    try:
        # 1. Income (Checkouts)
        checkouts_query = db.query(Checkout).order_by(Checkout.checkout_date.desc())
        if branch_id is not None:
            checkouts_query = checkouts_query.filter(Checkout.branch_id == branch_id)
            
        checkouts = checkouts_query.limit(limit).all()
        for c in checkouts:
            transactions.append({
                "id": f"INC-{c.id}",
                "type": "Income",
                "category": "Checkout",
                "description": f"Room {c.room_number} - {c.guest_name}",
                "amount": float(c.grand_total or 0),
                "date": c.checkout_date,
                "is_income": True
            })

        # 2. Expenses
        expenses_query = db.query(Expense).order_by(Expense.date.desc())
        if branch_id is not None:
            expenses_query = expenses_query.filter(Expense.branch_id == branch_id)
            
        expenses = expenses_query.limit(limit).all()
        for e in expenses:
            transactions.append({
                "id": f"EXP-{e.id}",
                "type": "Expense",
                "category": e.category,
                "description": e.description or "General Expense",
                "amount": float(e.amount or 0),
                "date": datetime.combine(e.date, datetime.min.time()) if isinstance(e.date, date) else e.date,
                "is_income": False
            })
            
        # 3. Purchases
        purchases_query = db.query(PurchaseMaster).order_by(PurchaseMaster.purchase_date.desc())
        if branch_id is not None:
            purchases_query = purchases_query.filter(PurchaseMaster.branch_id == branch_id)
            
        purchases = purchases_query.limit(limit).all()
        for p in purchases:
            transactions.append({
                "id": f"PUR-{p.id}",
                "type": "Expense",
                "category": "Inventory Purchase",
                "description": f"PO {p.purchase_number} - {p.vendor.name if p.vendor else 'Unknown'}",
                "amount": float(p.total_amount or 0),
                "date": datetime.combine(p.purchase_date, datetime.min.time()) if isinstance(p.purchase_date, date) else p.purchase_date,
                "is_income": False
            })

        # Sort
        transactions.sort(key=lambda x: x['date'] or datetime.min, reverse=True)
    except Exception as e:
        print(f"Error fetching transactions: {e}")
        
    return transactions[:limit]

@router.get("/pnl")
def get_pnl(
    period: str = "month",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):
    """
    Get P&L Statement data.
    """
    if period != "custom":
        start_date, end_date = get_date_range(period)
    
    def apply_date_filter(query, date_column):
        if start_date:
            query = query.filter(date_column >= start_date)
        if end_date:
            query = query.filter(date_column < end_date)
        return query

    # Revenue
    revenue_q = apply_date_filter(db.query(Checkout), Checkout.checkout_date)
    if branch_id is not None:
        revenue_q = revenue_q.filter(Checkout.branch_id == branch_id)
        
    room_rev = float(revenue_q.with_entities(func.sum(Checkout.room_total)).scalar() or 0)
    food_rev = float(revenue_q.with_entities(func.sum(Checkout.food_total)).scalar() or 0)
    service_rev = float(revenue_q.with_entities(func.sum(Checkout.service_total)).scalar() or 0)
    other_rev = float(revenue_q.with_entities(func.sum(Checkout.package_total)).scalar() or 0)
    total_rev = room_rev + food_rev + service_rev + other_rev
    
    # Expenses
    # Operational
    exp_q = apply_date_filter(db.query(Expense.category, func.sum(Expense.amount)).group_by(Expense.category), Expense.date)
    if branch_id is not None:
        exp_q = exp_q.filter(Expense.branch_id == branch_id)
        
    expenses_by_cat = [{"category": c, "amount": float(a or 0)} for c, a in exp_q.all()]
    total_ops_exp = sum(e['amount'] for e in expenses_by_cat)
    
    # Purchases
    purch_q = apply_date_filter(db.query(PurchaseMaster), PurchaseMaster.purchase_date)
    if branch_id is not None:
        purch_q = purch_q.filter(PurchaseMaster.branch_id == branch_id)
        
    total_purchase = float(purch_q.with_entities(func.sum(PurchaseMaster.total_amount)).scalar() or 0)
    
    total_exp = total_ops_exp + total_purchase

    # Revenue Breakdown by Payment Mode
    payment_breakdown = {}
    try:
        # Fix: Use payment_method instead of payment_mode
        mode_q = apply_date_filter(db.query(Checkout.payment_method, func.sum(Checkout.grand_total)), func.cast(Checkout.checkout_date, Date))
        if branch_id is not None:
            mode_q = mode_q.filter(Checkout.branch_id == branch_id)
            
        results = mode_q.group_by(Checkout.payment_method).all()
        for mode, amt in results:
            if mode: 
                payment_breakdown[mode] = float(amt or 0)
    except Exception as e:
        print(f"Error in PnL payment mode breakdown: {e}")
    
    return {
        "revenue": {
            "room": room_rev,
            "food": food_rev,
            "service": service_rev,
            "other": other_rev,
            "total": total_rev,
            "by_mode": payment_breakdown
        },
        "expenses": {
            "operational": expenses_by_cat,
            "purchases": total_purchase,
            "total": total_exp
        },
        "net_profit": total_rev - total_exp
    }

@router.get("/department/{dept_name}")
def get_department_details(
    dept_name: str,
    period: str = "month",
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if period != "custom":
        start_date, end_date = get_date_range(period)
    
    def apply_date(q, col):
        if start_date: 
            q = q.filter(col >= start_date)
        if end_date: 
            q = q.filter(col <= end_date)
        return q

    # 1. Expenses
    exp_q = db.query(func.sum(Expense.amount)).filter(Expense.department == dept_name)
    exp_q = apply_date(exp_q, Expense.date)
    total_expenses = exp_q.scalar() or 0.0

    # 2. Income (Approximation)
    total_income = 0.0
    if dept_name == "Restaurant":
         inc_q = db.query(func.sum(FoodOrder.total_amount)).filter(FoodOrder.status != "Cancelled")
         if start_date: inc_q = inc_q.filter(func.date(FoodOrder.created_at) >= start_date)
         if end_date: inc_q = inc_q.filter(func.date(FoodOrder.created_at) <= end_date)
         total_income = inc_q.scalar() or 0.0
    
    # 3. Assets (Fixed assets in this department)
    total_assets = 0.0
    try:
        # Fixed assets explicitly marked
        fixed_assets_query = db.query(
            func.sum(func.abs(InventoryItem.current_stock) * InventoryItem.unit_price)
        ).join(InventoryCategory).filter(
            InventoryCategory.parent_department == dept_name,
            InventoryItem.is_asset_fixed == True,
            InventoryItem.current_stock != 0
        )
        fixed_assets = fixed_assets_query.scalar() or 0
        
        # High-value items (likely assets even if not marked)
        high_value_query = db.query(
            func.sum(func.abs(InventoryItem.current_stock) * InventoryItem.unit_price)
        ).join(InventoryCategory).filter(
            InventoryCategory.parent_department == dept_name,
            InventoryItem.is_asset_fixed == False,
            InventoryItem.unit_price >= 10000,
            InventoryItem.current_stock != 0
        )
        high_value_assets = high_value_query.scalar() or 0
        
        total_assets = float(fixed_assets) + float(high_value_assets)
    except Exception as e:
        print(f"Error calculating assets for {dept_name}: {e}")
        total_assets = 0.0
    
    # 4. Capital Investment (Inventory purchases for this department)
    # Use same logic as summary endpoint for consistency
    capital_investment = 0.0
    try:
        from app.models.inventory import PurchaseDetail
        purchase_query = db.query(PurchaseDetail).join(PurchaseMaster)
        purchase_query = apply_date(purchase_query, PurchaseMaster.purchase_date)
        
        # Join with InventoryItem and InventoryCategory to filter by department
        dept_purchases = purchase_query.join(
            InventoryItem, PurchaseDetail.item_id == InventoryItem.id
        ).join(
            InventoryCategory, InventoryItem.category_id == InventoryCategory.id
        ).filter(
            InventoryCategory.parent_department == dept_name
        ).with_entities(func.sum(PurchaseDetail.total_amount)).scalar() or 0
        
        capital_investment = float(dept_purchases) if dept_purchases else 0.0
    except Exception as e:
        print(f"Error calculating capital investment for {dept_name}: {e}")
        capital_investment = 0.0
    
    # 5. Inventory Consumption (Stock Issued to Dept locations)
    inventory_consumption = 0.0
    try:
        locs = db.query(Location.id).filter(Location.name.ilike(f"%{dept_name}%")).all()
        loc_ids = [l[0] for l in locs]
        
        if loc_ids:
            cons_q = db.query(func.sum(StockIssueDetail.quantity * InventoryItem.unit_price))\
                .select_from(StockIssueDetail)\
                .join(StockIssue)\
                .join(InventoryItem)\
                .filter(StockIssue.destination_location_id.in_(loc_ids))
            
            cons_q = apply_date(cons_q, StockIssue.created_at)
            inventory_consumption = cons_q.scalar() or 0.0
    except Exception as e:
        print(f"Error calculating inventory consumption for {dept_name}: {e}")
        inventory_consumption = 0.0

    return {
        "department": dept_name,
        "income": round(float(total_income), 2),
        "expenses": round(float(total_expenses), 2),
        "regular_expenses": round(float(total_expenses), 2),
        "inventory_consumption": round(float(inventory_consumption), 2),
        "capital_investment": round(capital_investment, 2),
        "assets": round(total_assets, 2)
    }

@router.get("/vendors/stats")
def get_vendor_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):
    vendors_query = db.query(Vendor)
    if branch_id is not None:
        vendors_query = vendors_query.filter(Vendor.branch_id == branch_id)
    vendors = vendors_query.all()
    stats = []
    
    for v in vendors:
        # 1. Total Purchases (Amount owed to vendor)
        purch_query = db.query(func.sum(PurchaseMaster.total_amount)).filter(PurchaseMaster.vendor_id == v.id)
        if branch_id is not None:
            purch_query = purch_query.filter(PurchaseMaster.branch_id == branch_id)
        purch_total = purch_query.scalar() or 0.0
            
        # 2. Total Payments (Expenses linked to Vendor - payments made)
        # Note: Expense model doesn't have a status field
        pay_query = db.query(func.sum(Expense.amount)).filter(Expense.vendor_id == v.id)
        if branch_id is not None:
            pay_query = pay_query.filter(Expense.branch_id == branch_id)
        pay_total = pay_query.scalar() or 0.0
            
        # Balance = What we owe (purchases) - What we've paid (expenses)
        balance = float(purch_total) - float(pay_total)
        
        if purch_total > 0 or pay_total > 0:
            stats.append({
                "id": v.id,
                "name": v.name,
                "company_name": v.company_name,
                "total_purchases": round(float(purch_total), 2),
                "total_payments": round(float(pay_total), 2),
                "balance": round(balance, 2)
            })
            
    stats.sort(key=lambda x: x['balance'], reverse=True)
    return stats

@router.get("/financial-trends")
def get_financial_trends(db: Session = Depends(get_db), branch_id: int = Depends(get_branch_id)):
    """
    Returns monthly revenue, expense, and profit for the last 6 months.
    """
    trends = []
    today = date.today()
    
    for i in range(5, -1, -1):
        # Calculate month date (approx)
        month_date = date(today.year, today.month, 1)
        # Go back i months
        y = month_date.year
        m = month_date.month - i
        while m <= 0:
            m += 12
            y -= 1
        
        start_date = date(y, m, 1)
        next_m = m + 1
        next_y = y
        if next_m > 12:
            next_m = 1
            next_y += 1
        end_date = date(next_y, next_m, 1)
        
        label = start_date.strftime("%b %Y")
        
        # Queries (Optimized/Simplified)
        rev_q = db.query(func.sum(Checkout.grand_total)).filter(Checkout.checkout_date >= start_date, Checkout.checkout_date < end_date)
        if branch_id is not None:
            rev_q = rev_q.filter(Checkout.branch_id == branch_id)
        rev = float(rev_q.scalar() or 0.0)
        
        exp_q = db.query(func.sum(Expense.amount)).filter(Expense.date >= start_date, Expense.date < end_date)
        if branch_id is not None:
            exp_q = exp_q.filter(Expense.branch_id == branch_id)
        exp = float(exp_q.scalar() or 0.0)
        
        purch_q = db.query(func.sum(PurchaseMaster.total_amount)).filter(PurchaseMaster.purchase_date >= start_date, PurchaseMaster.purchase_date < end_date)
        if branch_id is not None:
            purch_q = purch_q.filter(PurchaseMaster.branch_id == branch_id)
        purch = float(purch_q.scalar() or 0.0)
        
        total_exp = exp + purch
        profit = rev - total_exp
        
        trends.append({
            "month": label,
            "revenue": round(float(rev), 2),
            "expense": round(float(total_exp), 2),
            "profit": round(float(profit), 2)
        })
        
    return trends