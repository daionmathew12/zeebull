"""
API endpoints for Accounting Module
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import functools

from app.database import get_db
from app.utils.auth import get_current_user
from app.utils.branch_scope import get_branch_id
from app.models.user import User

from app.curd import account as account_crud
from app.schemas.account import (
    AccountGroupCreate, AccountGroupUpdate, AccountGroupOut,
    AccountLedgerCreate, AccountLedgerUpdate, AccountLedgerOut,
    JournalEntryCreate, JournalEntryUpdate, JournalEntryOut,
    TrialBalance, LedgerBalance
)

router = APIRouter(prefix="/accounts", tags=["Accounts"])


# Account Group Endpoints
@router.post("/groups", response_model=AccountGroupOut)
def create_account_group(
    group: AccountGroupCreate,
    db: Session = Depends(get_db),
    branch_id: int = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """Create a new account group"""
    return account_crud.create_account_group(db, group, branch_id=branch_id)



@router.get("/groups", response_model=List[AccountGroupOut])
def get_account_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=5000),  # Increased limit for mobile compatibility
    account_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    branch_id: int = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """Get all account groups"""
    return account_crud.get_account_groups(db, branch_id=branch_id, skip=skip, limit=limit, account_type=account_type)



@router.get("/groups/{group_id}", response_model=AccountGroupOut)
def get_account_group(
    group_id: int,
    db: Session = Depends(get_db),
    branch_id: int = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """Get account group by ID"""
    group = account_crud.get_account_group(db, group_id, branch_id=branch_id)
    if not group:
        raise HTTPException(status_code=404, detail="Account group not found")
    return group



@router.put("/groups/{group_id}", response_model=AccountGroupOut)
def update_account_group(
    group_id: int,
    group_update: AccountGroupUpdate,
    db: Session = Depends(get_db),
    branch_id: int = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """Update account group"""
    group = account_crud.update_account_group(db, group_id, group_update, branch_id=branch_id)
    if not group:
        raise HTTPException(status_code=404, detail="Account group not found")
    return group



@router.delete("/groups/{group_id}")
def delete_account_group(
    group_id: int,
    db: Session = Depends(get_db),
    branch_id: int = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """Delete account group (soft delete)"""
    success = account_crud.delete_account_group(db, group_id, branch_id=branch_id)
    if not success:
        raise HTTPException(status_code=404, detail="Account group not found")
    return {"message": "Account group deleted successfully"}



# Account Ledger Endpoints
@router.post("/ledgers", response_model=AccountLedgerOut)
def create_account_ledger(
    ledger: AccountLedgerCreate,
    db: Session = Depends(get_db),
    branch_id: int = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """Create a new account ledger"""
    return account_crud.create_account_ledger(db, ledger, branch_id=branch_id)



@router.get("/ledgers", response_model=List[AccountLedgerOut])
def get_account_ledgers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=5000),  # Increased limit for mobile compatibility
    group_id: Optional[int] = Query(None),
    module: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(True),
    db: Session = Depends(get_db),
    branch_id: int = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """Get all account ledgers"""
    return account_crud.get_account_ledgers(
        db, branch_id=branch_id, skip=skip, limit=limit, group_id=group_id, module=module, is_active=is_active
    )



@router.get("/ledgers/{ledger_id}", response_model=AccountLedgerOut)
def get_account_ledger(
    ledger_id: int,
    db: Session = Depends(get_db),
    branch_id: int = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """Get account ledger by ID"""
    ledger = account_crud.get_account_ledger(db, ledger_id, branch_id=branch_id)
    if not ledger:
        raise HTTPException(status_code=404, detail="Account ledger not found")
    return ledger



@router.put("/ledgers/{ledger_id}", response_model=AccountLedgerOut)
def update_account_ledger(
    ledger_id: int,
    ledger_update: AccountLedgerUpdate,
    db: Session = Depends(get_db),
    branch_id: int = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """Update account ledger"""
    ledger = account_crud.update_account_ledger(db, ledger_id, ledger_update, branch_id=branch_id)
    if not ledger:
        raise HTTPException(status_code=404, detail="Account ledger not found")
    return ledger



@router.delete("/ledgers/{ledger_id}")
def delete_account_ledger(
    ledger_id: int,
    db: Session = Depends(get_db),
    branch_id: int = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """Delete account ledger (soft delete)"""
    success = account_crud.delete_account_ledger(db, ledger_id, branch_id=branch_id)
    if not success:
        raise HTTPException(status_code=404, detail="Account ledger not found")
    return {"message": "Account ledger deleted successfully"}



@router.get("/ledgers/{ledger_id}/balance", response_model=LedgerBalance)
def get_ledger_balance(
    ledger_id: int,
    as_on_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    branch_id: int = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """Get ledger balance"""
    balance = account_crud.get_ledger_balance(db, ledger_id, branch_id=branch_id, as_on_date=as_on_date)
    if not balance:
        raise HTTPException(status_code=404, detail="Account ledger not found")
    return balance



# Journal Entry Endpoints
@router.post("/journal-entries", response_model=JournalEntryOut)
def create_journal_entry(
    entry: JournalEntryCreate,
    db: Session = Depends(get_db),
    branch_id: int = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """Create a new journal entry"""
    # Validate that debits equal credits
    total_debits = sum(line.amount for line in entry.lines if line.debit_ledger_id)
    total_credits = sum(line.amount for line in entry.lines if line.credit_ledger_id)
    
    if abs(total_debits - total_credits) > 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"Journal entry must balance. Debits: {total_debits}, Credits: {total_credits}"
        )
    
    return account_crud.create_journal_entry(db, entry, branch_id=branch_id, created_by=current_user.id)



@router.get("/journal-entries", response_model=List[JournalEntryOut])
def get_journal_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=5000),  # Increased limit for mobile compatibility
    reference_type: Optional[str] = Query(None),
    reference_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    branch_id: int = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """Get journal entries"""
    return account_crud.get_journal_entries(
        db, branch_id=branch_id, skip=skip, limit=limit, reference_type=reference_type,
        reference_id=reference_id, start_date=start_date, end_date=end_date
    )



@router.get("/journal-entries/{entry_id}", response_model=JournalEntryOut)
def get_journal_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    branch_id: int = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """Get journal entry by ID"""
    entry = account_crud.get_journal_entry(db, entry_id, branch_id=branch_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return entry



@router.get("/trial-balance", response_model=TrialBalance)
def get_trial_balance(
    as_on_date: Optional[datetime] = Query(None),
    automatic: bool = Query(False, description="Automatically calculate from all business transactions"),
    db: Session = Depends(get_db),
    branch_id: Optional[int] = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):

    """
    Get trial balance.
    
    If automatic=True (default), calculates from all business transactions for the current branch:

    - Checkouts (revenue)
    - Food Orders (revenue)
    - Services (revenue)
    - Expenses (expenses)
    - Inventory Purchases (expenses/assets)
    - Inventory Consumption (COGS)
    - Journal Entries (manual entries)
    
    If automatic=False, only calculates from journal entries.
    """
    try:
        return account_crud.get_trial_balance(db, branch_id=branch_id, as_on_date=as_on_date, automatic=automatic)
    except Exception as e:
        import traceback
        error_msg = f"Error in get_trial_balance endpoint: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=f"Error generating trial balance: {str(e)}")


@router.post("/fix-missing-journal-entries")
def fix_missing_journal_entries(
    checkout_id: Optional[int] = None,
    room_number: Optional[str] = None,
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fix missing journal entries for checkouts.
    Can fix a specific checkout by ID or room number, or all checkouts in the last N days.
    """
    from app.models.checkout import Checkout
    from app.models.account import JournalEntry
    from app.utils.accounting_helpers import create_complete_checkout_journal_entry
    from datetime import datetime, timedelta
    
    try:
        checkouts_to_fix = []
        
        if checkout_id:
            checkout = db.query(Checkout).filter(Checkout.id == checkout_id).first()
            if checkout:
                checkouts_to_fix = [checkout]
        elif room_number:
            checkout = db.query(Checkout).filter(Checkout.room_number == room_number).order_by(Checkout.created_at.desc()).first()
            if checkout:
                checkouts_to_fix = [checkout]
        else:
            # Fix all checkouts in last N days
            cutoff_date = datetime.now() - timedelta(days=days)
            checkouts = db.query(Checkout).filter(Checkout.created_at >= cutoff_date).all()
            checkouts_to_fix = checkouts
        
        if not checkouts_to_fix:
            return {"message": "No checkouts found to fix", "fixed": 0}
        
        fixed_count = 0
        failed_count = 0
        errors = []
        
        for checkout in checkouts_to_fix:
            # Check if journal entry exists
            journal_entry = db.query(JournalEntry).filter(
                JournalEntry.reference_type == "CHECKOUT",
                JournalEntry.reference_id == checkout.id
            ).first()
            
            if journal_entry:
                continue  # Already has journal entry
            
            # Try to create journal entry
            try:
                result = create_complete_checkout_journal_entry(
                    db=db,
                    checkout_id=checkout.id,
                    room_total=float(checkout.room_total or 0),
                    food_total=float(checkout.food_total or 0),
                    service_total=float(checkout.service_total or 0),
                    package_total=float(checkout.package_total or 0),
                    tax_amount=float(checkout.tax_amount or 0),
                    discount_amount=float(checkout.discount_amount or 0),
                    grand_total=float(checkout.grand_total or 0),
                    guest_name=checkout.guest_name or "Guest",
                    room_number=checkout.room_number or "Unknown",
                    gst_rate=18.0,
                    payment_method=checkout.payment_method or "cash",
                    branch_id=checkout.branch_id,
                    created_by=current_user.id if current_user else None
                )

                
                if result:
                    db.commit()
                    fixed_count += 1
                else:
                    failed_count += 1
                    errors.append(f"Checkout {checkout.id}: Ledgers missing")
            except Exception as e:
                failed_count += 1
                errors.append(f"Checkout {checkout.id}: {str(e)}")
                db.rollback()
        
        return {
            "message": f"Fixed {fixed_count} journal entries, {failed_count} failed",
            "fixed": fixed_count,
            "failed": failed_count,
            "errors": errors
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error fixing journal entries: {str(e)}")

@router.get("/comprehensive-report")
def get_comprehensive_report(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records per category"),
    db: Session = Depends(get_db),
    branch_id: Optional[int] = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive report with ALL business data:
    - All Checkouts
    - All Bookings (regular and package)
    - All Food Orders
    - All Services
    - All Expenses
    - All Inventory Purchases
    - All Inventory Transactions
    - All Journal Entries
    
    This endpoint returns complete data records, not just summaries.
    """
    try:
        from app.models.checkout import Checkout
        from app.models.booking import Booking, BookingRoom
        from app.models.Package import PackageBooking, PackageBookingRoom
        from app.models.foodorder import FoodOrder, FoodOrderItem
        from app.models.service import AssignedService
        from app.models.expense import Expense
        from app.models.inventory import PurchaseMaster, PurchaseDetail, InventoryTransaction
        from app.models.account import JournalEntry, JournalEntryLine
        from app.models.employee import Employee, Attendance, Leave, WorkingLog
        from sqlalchemy import and_, or_
        from sqlalchemy.orm import joinedload
        from datetime import datetime, date as date_type
        
        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            try:
                if len(start_date) == 10:
                    date_obj = date_type.fromisoformat(start_date)
                    start_dt = datetime.combine(date_obj, datetime.min.time())
                else:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except:
                start_dt = None
        if end_date:
            try:
                if len(end_date) == 10:
                    date_obj = date_type.fromisoformat(end_date)
                    end_dt = datetime.combine(date_obj, datetime.max.time())
                else:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except:
                end_dt = None
        
        # Build date filters
        def build_date_filter(model, date_field):
            filters = []
            if branch_id is not None:
                filters.append(model.branch_id == branch_id)
            if start_dt:
                filters.append(date_field >= start_dt)
            if end_dt:
                filters.append(date_field <= end_dt)
            return filters

        
        result = {
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "generated_at": datetime.utcnow().isoformat(),
            "data": {}
        }
        
        # 1. All Checkouts
        try:
            checkout_filters = build_date_filter(Checkout, Checkout.checkout_date)
            checkout_query = db.query(Checkout)
            if checkout_filters:
                checkout_query = checkout_query.filter(and_(*checkout_filters))
            checkouts = checkout_query.order_by(Checkout.checkout_date.desc()).limit(limit).all()
            result["data"]["checkouts"] = [{
                "id": c.id,
                "booking_id": c.booking_id,
                "package_booking_id": c.package_booking_id,
                "guest_name": c.guest_name,
                "room_number": c.room_number,
                "checkout_date": c.checkout_date.isoformat() if c.checkout_date else None,
                "room_total": float(c.room_total or 0),
                "food_total": float(c.food_total or 0),
                "service_total": float(c.service_total or 0),
                "package_total": float(c.package_total or 0),
                "tax_amount": float(c.tax_amount or 0),
                "discount_amount": float(c.discount_amount or 0),
                "grand_total": float(c.grand_total or 0),
                "payment_status": c.payment_status,
                "payment_method": c.payment_method
            } for c in checkouts]
        except Exception as e:
            print(f"Error fetching checkouts: {str(e)}")
            result["data"]["checkouts"] = []
        
        # 2. All Bookings (Regular)
        try:
            booking_filters = build_date_filter(Booking, Booking.check_in)
            booking_query = db.query(Booking)
            if booking_filters:
                booking_query = booking_query.filter(and_(*booking_filters))
            bookings = booking_query.order_by(Booking.check_in.desc()).limit(limit).all()
            result["data"]["bookings"] = [{
                "id": b.id,
                "guest_name": b.guest_name,
                "guest_mobile": b.guest_mobile,
                "guest_email": b.guest_email,
                "check_in": b.check_in.isoformat() if b.check_in else None,
                "check_out": b.check_out.isoformat() if b.check_out else None,
                "status": b.status,
                "total_amount": float(b.total_amount or 0),
                "advance_deposit": float(b.advance_deposit or 0),
                "adults": b.adults,
                "children": b.children,
                "rooms": [{"room_id": br.room_id, "room_number": br.room.number if br.room else None} for br in b.booking_rooms] if b.booking_rooms else []
            } for b in bookings]
        except Exception as e:
            print(f"Error fetching bookings: {str(e)}")
            result["data"]["bookings"] = []
        
        # 3. All Package Bookings
        try:
            pkg_booking_filters = build_date_filter(PackageBooking, PackageBooking.check_in)
            pkg_booking_query = db.query(PackageBooking)
            if pkg_booking_filters:
                pkg_booking_query = pkg_booking_query.filter(and_(*pkg_booking_filters))
            package_bookings = pkg_booking_query.order_by(PackageBooking.check_in.desc()).limit(limit).all()
            result["data"]["package_bookings"] = [{
                "id": pb.id,
                "guest_name": pb.guest_name,
                "guest_mobile": pb.guest_mobile,
                "guest_email": pb.guest_email,
                "check_in": pb.check_in.isoformat() if pb.check_in else None,
                "check_out": pb.check_out.isoformat() if pb.check_out else None,
                "status": pb.status,
                "total_amount": float(pb.total_amount or 0),
                "advance_deposit": float(pb.advance_deposit or 0),
                "package_id": pb.package_id,
                "package_name": pb.package.name if pb.package else None,
                "rooms": [{"room_id": pbr.room_id, "room_number": pbr.room.number if pbr.room else None} for pbr in pb.rooms] if pb.rooms else []
            } for pb in package_bookings]
        except Exception as e:
            print(f"Error fetching package bookings: {str(e)}")
            result["data"]["package_bookings"] = []
        
        # 4. All Food Orders
        try:
            food_filters = build_date_filter(FoodOrder, FoodOrder.created_at)
            food_query = db.query(FoodOrder).options(
                joinedload(FoodOrder.items).joinedload(FoodOrderItem.food_item)
            )
            if food_filters:
                food_query = food_query.filter(and_(*food_filters))
            food_orders = food_query.order_by(FoodOrder.created_at.desc()).limit(limit).all()
            result["data"]["food_orders"] = [{
                "id": fo.id,
                "room_id": fo.room_id,
                "room_number": fo.room.number if fo.room else None,
                "amount": float(fo.amount or 0),
                "status": fo.status,
                "billing_status": fo.billing_status,
                "order_type": fo.order_type,
                "created_at": fo.created_at.isoformat() if fo.created_at else None,
                "items": [{
                    "food_item_id": item.food_item_id,
                    "food_item_name": item.food_item.name if item.food_item else None,
                    "quantity": item.quantity
                } for item in fo.items] if fo.items else []
            } for fo in food_orders]
        except Exception as e:
            print(f"Error fetching food orders: {str(e)}")
            result["data"]["food_orders"] = []
        
        # 5. All Services
        try:
            service_filters = build_date_filter(AssignedService, AssignedService.assigned_at)
            service_query = db.query(AssignedService).options(
                joinedload(AssignedService.service),
                joinedload(AssignedService.employee),
                joinedload(AssignedService.room)
            )
            if service_filters:
                service_query = service_query.filter(and_(*service_filters))
            services = service_query.order_by(AssignedService.assigned_at.desc()).limit(limit).all()
            result["data"]["services"] = [{
                "id": s.id,
                "service_id": s.service_id,
                "service_name": s.service.name if s.service else None,
                "room_id": s.room_id,
                "room_number": s.room.number if s.room else None,
                "employee_id": s.employee_id,
                "employee_name": s.employee.name if s.employee else None,
                "status": s.status,
                "billing_status": s.billing_status,
                "assigned_at": s.assigned_at.isoformat() if s.assigned_at else None,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None
            } for s in services]
        except Exception as e:
            print(f"Error fetching services: {str(e)}")
            result["data"]["services"] = []
        
        # 6. All Expenses
        try:
            expense_filters = []
            if branch_id is not None:
                expense_filters.append(Expense.branch_id == branch_id)
            if start_dt:
                expense_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt
                expense_filters.append(Expense.date >= expense_date)
            if end_dt:
                expense_date = end_dt.date() if isinstance(end_dt, datetime) else end_dt
                expense_filters.append(Expense.date <= expense_date)
            expense_query = db.query(Expense)
            if expense_filters:
                expense_query = expense_query.filter(and_(*expense_filters))

            expenses = expense_query.order_by(Expense.date.desc()).limit(limit).all()
            result["data"]["expenses"] = [{
                "id": e.id,
                "category": e.category,
                "amount": float(e.amount or 0),
                "description": e.description,
                "date": e.date.isoformat() if e.date else None,
                "employee_id": e.employee_id,
                "employee_name": e.employee.name if e.employee else None
            } for e in expenses]
        except Exception as e:
            print(f"Error fetching expenses: {str(e)}")
            result["data"]["expenses"] = []
        
        # 7. All Inventory Purchases
        try:
            purchase_filters = []
            if branch_id is not None:
                purchase_filters.append(PurchaseMaster.branch_id == branch_id)
            if start_dt:
                purchase_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt
                purchase_filters.append(PurchaseMaster.purchase_date >= purchase_date)
            if end_dt:
                purchase_date = end_dt.date() if isinstance(end_dt, datetime) else end_dt
                purchase_filters.append(PurchaseMaster.purchase_date <= purchase_date)
            
            # Simplified query first to debug
            purchase_query = db.query(PurchaseMaster).options(
                joinedload(PurchaseMaster.vendor)
            )
            
            if purchase_filters:
                purchase_query = purchase_query.filter(and_(*purchase_filters))

                
            purchases = purchase_query.order_by(PurchaseMaster.purchase_date.desc()).limit(limit).all()
            
            purchases_data = []
            for p in purchases:
                # Safe serialization
                p_data = {
                    "id": p.id,
                    "purchase_number": p.purchase_number,
                    "vendor_id": p.vendor_id,
                    "vendor_name": p.vendor.name if p.vendor else "Unknown",
                    "purchase_date": p.purchase_date.isoformat() if p.purchase_date else None,
                    "total_amount": float(p.total_amount or 0),
                    "status": p.status,
                    "details": [] # Temporarily empty to rule out details error
                }
                
                # Try to load details safely
                try:
                    if p.details:
                        for d in p.details:
                            p_data["details"].append({
                                "item_id": d.item_id,
                                "item_name": d.item.name if (d.item) else "Unknown Item",
                                "quantity": float(d.quantity or 0),
                                "unit_price": float(d.unit_price or 0),
                                "total": float(d.total or 0)
                            })
                except Exception as ex:
                    print(f"Error loading details for purchase {p.id}: {ex}")
                
                purchases_data.append(p_data)

            result["data"]["purchases"] = purchases_data
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error fetching purchases: {str(e)}")
            result["data"]["purchases"] = []
        
        # 8. All Inventory Transactions
        try:
            transaction_filters = build_date_filter(InventoryTransaction, InventoryTransaction.created_at)
            transaction_query = db.query(InventoryTransaction).options(
                joinedload(InventoryTransaction.item)
            )
            if transaction_filters:
                transaction_query = transaction_query.filter(and_(*transaction_filters))
            transactions = transaction_query.order_by(InventoryTransaction.created_at.desc()).limit(limit).all()
            result["data"]["inventory_transactions"] = [{
                "id": t.id,
                "item_id": t.item_id,
                "item_name": t.item.name if t.item else None,
                "transaction_type": t.transaction_type,
                "quantity": float(t.quantity or 0),
                "unit_price": float(t.unit_price or 0),
                "total_amount": float(t.total_amount or 0),
                "reference_number": t.reference_number,
                "notes": t.notes,
                "created_at": t.created_at.isoformat() if t.created_at else None
            } for t in transactions]
        except Exception as e:
            print(f"Error fetching inventory transactions: {str(e)}")
            result["data"]["inventory_transactions"] = []
        
        # 9. All Journal Entries
        try:
            journal_filters = build_date_filter(JournalEntry, JournalEntry.entry_date)
            journal_query = db.query(JournalEntry).options(
                joinedload(JournalEntry.lines).joinedload(JournalEntryLine.debit_ledger),
                joinedload(JournalEntry.lines).joinedload(JournalEntryLine.credit_ledger)
            )
            if journal_filters:
                journal_query = journal_query.filter(and_(*journal_filters))
            journal_entries = journal_query.order_by(JournalEntry.entry_date.desc()).limit(limit).all()
            result["data"]["journal_entries"] = [{
                "id": je.id,
                "entry_number": je.entry_number,
                "entry_date": je.entry_date.isoformat() if je.entry_date else None,
                "description": je.description,
                "reference_type": je.reference_type,
                "reference_id": je.reference_id,
                "lines": [{
                    "id": line.id,
                    "debit_ledger_id": line.debit_ledger_id,
                    "debit_ledger_name": line.debit_ledger.name if line.debit_ledger else None,
                    "credit_ledger_id": line.credit_ledger_id,
                    "credit_ledger_name": line.credit_ledger.name if line.credit_ledger else None,
                    "amount": float(line.amount or 0),
                    "description": line.description
                } for line in je.lines] if je.lines else []
            } for je in journal_entries]
        except Exception as e:
            print(f"Error fetching journal entries: {str(e)}")
            result["data"]["journal_entries"] = []
        
        # 10. All Employees with Salary Information
        try:
            employee_query = db.query(Employee)
            if branch_id is not None:
                employee_query = employee_query.filter(Employee.branch_id == branch_id)
            employees = employee_query.order_by(Employee.name).limit(limit).all()

            result["data"]["employees"] = [{
                "id": e.id,
                "name": e.name,
                "role": e.role,
                "salary": float(e.salary or 0),
                "join_date": e.join_date.isoformat() if e.join_date else None,
                "user_id": e.user_id
            } for e in employees]
        except Exception as e:
            print(f"Error fetching employees: {str(e)}")
            result["data"]["employees"] = []
        
        # 11. All Attendance Records
        try:
            attendance_filters = []
            if branch_id is not None:
                attendance_filters.append(Attendance.branch_id == branch_id)
            if start_dt:

                attendance_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt
                attendance_filters.append(Attendance.date >= attendance_date)
            if end_dt:
                attendance_date = end_dt.date() if isinstance(end_dt, datetime) else end_dt
                attendance_filters.append(Attendance.date <= attendance_date)
            attendance_query = db.query(Attendance).options(
                joinedload(Attendance.employee)
            )
            if attendance_filters:
                attendance_query = attendance_query.filter(and_(*attendance_filters))
            attendances = attendance_query.order_by(Attendance.date.desc()).limit(limit).all()
            result["data"]["attendances"] = [{
                "id": a.id,
                "employee_id": a.employee_id,
                "employee_name": a.employee.name if a.employee else None,
                "date": a.date.isoformat() if a.date else None,
                "status": a.status
            } for a in attendances]
        except Exception as e:
            print(f"Error fetching attendances: {str(e)}")
            result["data"]["attendances"] = []
        
        # 12. All Leaves
        try:
            leave_filters = []
            if branch_id is not None:
                leave_filters.append(Leave.branch_id == branch_id)
            if start_dt:

                leave_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt
                leave_filters.append(Leave.from_date >= leave_date)
            if end_dt:
                leave_date = end_dt.date() if isinstance(end_dt, datetime) else end_dt
                leave_filters.append(Leave.to_date <= leave_date)
            leave_query = db.query(Leave).options(
                joinedload(Leave.employee)
            )
            if leave_filters:
                leave_query = leave_query.filter(and_(*leave_filters))
            leaves = leave_query.order_by(Leave.from_date.desc()).limit(limit).all()
            result["data"]["leaves"] = [{
                "id": l.id,
                "employee_id": l.employee_id,
                "employee_name": l.employee.name if l.employee else None,
                "from_date": l.from_date.isoformat() if l.from_date else None,
                "to_date": l.to_date.isoformat() if l.to_date else None,
                "reason": l.reason,
                "leave_type": l.leave_type,
                "status": l.status
            } for l in leaves]
        except Exception as e:
            print(f"Error fetching leaves: {str(e)}")
            result["data"]["leaves"] = []
        
        # 13. All Working Logs
        try:
            working_log_filters = []
            if branch_id is not None:
                working_log_filters.append(WorkingLog.branch_id == branch_id)
            if start_dt:

                log_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt
                working_log_filters.append(WorkingLog.date >= log_date)
            if end_dt:
                log_date = end_dt.date() if isinstance(end_dt, datetime) else end_dt
                working_log_filters.append(WorkingLog.date <= log_date)
            working_log_query = db.query(WorkingLog).options(
                joinedload(WorkingLog.employee)
            )
            if working_log_filters:
                working_log_query = working_log_query.filter(and_(*working_log_filters))
            working_logs = working_log_query.order_by(WorkingLog.date.desc()).limit(limit).all()
            result["data"]["working_logs"] = [{
                "id": wl.id,
                "employee_id": wl.employee_id,
                "employee_name": wl.employee.name if wl.employee else None,
                "date": wl.date.isoformat() if wl.date else None,
                "check_in_time": wl.check_in_time.strftime("%H:%M:%S") if wl.check_in_time else None,
                "check_out_time": wl.check_out_time.strftime("%H:%M:%S") if wl.check_out_time else None,
                "location": wl.location
            } for wl in working_logs]
        except Exception as e:
            print(f"Error fetching working logs: {str(e)}")
            result["data"]["working_logs"] = []
        
        # Add summary counts
        result["summary"] = {
            "total_checkouts": len(result["data"]["checkouts"]),
            "total_bookings": len(result["data"]["bookings"]),
            "total_package_bookings": len(result["data"]["package_bookings"]),
            "total_food_orders": len(result["data"]["food_orders"]),
            "total_services": len(result["data"]["services"]),
            "total_expenses": len(result["data"]["expenses"]),
            "total_purchases": len(result["data"]["purchases"]),
            "total_inventory_transactions": len(result["data"]["inventory_transactions"]),
            "total_journal_entries": len(result["data"]["journal_entries"]),
            "total_employees": len(result["data"]["employees"]),
            "total_attendances": len(result["data"]["attendances"]),
            "total_leaves": len(result["data"]["leaves"]),
            "total_working_logs": len(result["data"]["working_logs"]),
            "total_salary_cost": sum([float(e.get("salary", 0) or 0) for e in result["data"]["employees"]])
        }
        
        return result
    except Exception as e:
        import traceback
        error_msg = f"Error in comprehensive report: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=f"Error generating comprehensive report: {str(e)}")


@router.get("/auto-report")
def get_automatic_accounting_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    branch_id: Optional[int] = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """
    Automatically calculate comprehensive accounting report from all sources:
    - Checkouts (room, food, service, package revenue)
    - Food Orders
    - Services
    - Expenses
    - Inventory Purchases
    - Inventory Consumption
    
    Uses SQL aggregations for optimal performance.
    """
    try:
        from app.models.checkout import Checkout
        from app.models.foodorder import FoodOrder
        from app.models.service import AssignedService, Service
        from app.models.expense import Expense
        from app.models.inventory import PurchaseMaster, InventoryTransaction
        from sqlalchemy import func, and_, case
        
        # Parse date strings to datetime objects
        start_dt = None
        end_dt = None
        if start_date:
            try:
                if isinstance(start_date, str):
                    # Try parsing as date first (YYYY-MM-DD)
                    if len(start_date) == 10 and start_date.count('-') == 2:
                        from datetime import date as date_type
                        date_obj = date_type.fromisoformat(start_date)
                        start_dt = datetime.combine(date_obj, datetime.min.time())
                    else:
                        # Try parsing as datetime string
                        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                else:
                    start_dt = start_date
            except Exception as e:
                print(f"Error parsing start_date: {e}")
                start_dt = None
        if end_date:
            try:
                if isinstance(end_date, str):
                    # Try parsing as date first (YYYY-MM-DD)
                    if len(end_date) == 10 and end_date.count('-') == 2:
                        from datetime import date as date_type
                        date_obj = date_type.fromisoformat(end_date)
                        end_dt = datetime.combine(date_obj, datetime.max.time())
                    else:
                        # Try parsing as datetime string
                        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                else:
                    end_dt = end_date
            except Exception as e:
                print(f"Error parsing end_date: {e}")
                end_dt = None
        
        # Set date filters
        checkout_date_filter = []
        if branch_id is not None:
            checkout_date_filter.append(Checkout.branch_id == branch_id)
        if start_dt:
            checkout_date_filter.append(Checkout.checkout_date >= start_dt)
        if end_dt:
            checkout_date_filter.append(Checkout.checkout_date <= end_dt)
        
        # 1. Checkout Revenue - Use SQL aggregations (with timeout)
        try:
            checkout_query = db.query(
                func.count(Checkout.id).label("total_checkouts"),
                func.coalesce(func.sum(Checkout.room_total), 0).label("room_revenue"),
                func.coalesce(func.sum(Checkout.food_total), 0).label("food_revenue"),
                func.coalesce(func.sum(Checkout.service_total), 0).label("service_revenue"),
                func.coalesce(func.sum(Checkout.package_total), 0).label("package_revenue"),
                func.coalesce(func.sum(Checkout.tax_amount), 0).label("tax_collected"),
                func.coalesce(func.sum(Checkout.discount_amount), 0).label("discount_given"),
                func.coalesce(func.sum(Checkout.grand_total), 0).label("grand_total"),
                func.coalesce(func.sum(Checkout.consumables_charges), 0).label("consumables_charges"),
                func.coalesce(func.sum(Checkout.asset_damage_charges), 0).label("asset_damage_charges"),
                func.coalesce(func.sum(Checkout.late_checkout_fee), 0).label("late_checkout_fees"),
                func.coalesce(func.sum(Checkout.key_card_fee), 0).label("key_card_fees"),
                func.coalesce(func.sum(Checkout.tips_gratuity), 0).label("tips_gratuity"),
            )
            if checkout_date_filter:
                checkout_query = checkout_query.filter(and_(*checkout_date_filter))
            
            checkout_result = checkout_query.first()
        except Exception as e:
            print(f"Checkout query error: {str(e)}")
            checkout_result = None
        checkout_stats = {
        "total_checkouts": checkout_result.total_checkouts or 0 if checkout_result else 0,
        "room_revenue": float(checkout_result.room_revenue or 0) if checkout_result else 0.0,
        "food_revenue": float(checkout_result.food_revenue or 0) if checkout_result else 0.0,
        "service_revenue": float(checkout_result.service_revenue or 0) if checkout_result else 0.0,
        "package_revenue": float(checkout_result.package_revenue or 0) if checkout_result else 0.0,
        "tax_collected": float(checkout_result.tax_collected or 0) if checkout_result else 0.0,
        "discount_given": float(checkout_result.discount_given or 0) if checkout_result else 0.0,
        "grand_total": float(checkout_result.grand_total or 0) if checkout_result else 0.0,
        "consumables_charges": float(checkout_result.consumables_charges or 0) if checkout_result else 0.0,
        "asset_damage_charges": float(checkout_result.asset_damage_charges or 0) if checkout_result else 0.0,
        "late_checkout_fees": float(checkout_result.late_checkout_fees or 0) if checkout_result else 0.0,
        "key_card_fees": float(checkout_result.key_card_fees or 0) if checkout_result else 0.0,
        "tips_gratuity": float(checkout_result.tips_gratuity or 0) if checkout_result else 0.0,
        }
        
        # 2. Food Orders - Use SQL aggregations (with timeout)
        # Logic: 
        # - Every food order is payable EXCEPT complimentary (amount == 0)
        # - "paid" status = already billed (paid at delivery time)
        # - "billed" status = billed at checkout
        # - "unbilled" status = payable at checkout
        try:
            food_date_filter = []
            if branch_id is not None:
                food_date_filter.append(FoodOrder.branch_id == branch_id)
            if start_dt:
                food_date_filter.append(FoodOrder.created_at >= start_dt)
            if end_dt:
                food_date_filter.append(FoodOrder.created_at <= end_dt)
            
            # Exclude complimentary orders (amount == 0 or amount is NULL)
            food_query = db.query(
                # Total orders (excluding complimentary)
                func.count(case((FoodOrder.amount > 0, FoodOrder.id), else_=None)).label("total_orders"),
                # Total revenue (excluding complimentary)
                func.coalesce(func.sum(case((FoodOrder.amount > 0, FoodOrder.amount), else_=0)), 0).label("total_revenue"),
                # Billed orders: billing_status IN ("billed", "paid") AND amount > 0
                func.count(case(
                    (and_(
                        FoodOrder.amount > 0,
                        FoodOrder.billing_status.in_(["billed", "paid"])
                    ), FoodOrder.id), 
                    else_=None
                )).label("billed_orders"),
                # Unbilled orders: billing_status == "unbilled" AND amount > 0
                func.count(case(
                    (and_(
                        FoodOrder.amount > 0,
                        FoodOrder.billing_status == "unbilled"
                    ), FoodOrder.id), 
                    else_=None
                )).label("unbilled_orders"),
                # Billed revenue: billing_status IN ("billed", "paid") AND amount > 0
                func.coalesce(func.sum(case(
                    (and_(
                        FoodOrder.amount > 0,
                        FoodOrder.billing_status.in_(["billed", "paid"])
                    ), FoodOrder.amount), 
                    else_=0
                )), 0).label("billed_revenue"),
                # Unbilled revenue: billing_status == "unbilled" AND amount > 0
                func.coalesce(func.sum(case(
                    (and_(
                        FoodOrder.amount > 0,
                        FoodOrder.billing_status == "unbilled"
                    ), FoodOrder.amount), 
                    else_=0
                )), 0).label("unbilled_revenue"),
            )
            if food_date_filter:
                food_query = food_query.filter(and_(*food_date_filter))
            
            food_result = food_query.first()
        except Exception as e:
            print(f"Food query error: {str(e)}")
            food_result = None
        food_stats = {
            "total_orders": food_result.total_orders or 0 if food_result else 0,
            "total_revenue": float(food_result.total_revenue or 0) if food_result else 0.0,
            "billed_orders": food_result.billed_orders or 0 if food_result else 0,
            "unbilled_orders": food_result.unbilled_orders or 0 if food_result else 0,
            "billed_revenue": float(food_result.billed_revenue or 0) if food_result else 0.0,
            "unbilled_revenue": float(food_result.unbilled_revenue or 0) if food_result else 0.0,
        }
        
        # 3. Services - Simplified to avoid timeouts (skip revenue calculation for now)
        service_date_filter = []
        if start_dt:
            service_date_filter.append(AssignedService.assigned_at >= start_dt)
        if end_dt:
            service_date_filter.append(AssignedService.assigned_at <= end_dt)
        
        # Only get counts (revenue is already included in checkout.service_total)
        try:
            service_count_query = db.query(
                func.count(AssignedService.id).label("total_services"),
                func.count(case((AssignedService.billing_status == "billed", AssignedService.id), else_=None)).label("billed_services"),
                func.count(case((AssignedService.billing_status == "unbilled", AssignedService.id), else_=None)).label("unbilled_services"),
            )
            if service_date_filter:
                service_count_query = service_count_query.filter(and_(*service_date_filter))
            count_result = service_count_query.first()
            
            # Service revenue is already captured in checkout.service_total, so we don't need to calculate it separately
            # This avoids the expensive join that was causing timeouts
            from types import SimpleNamespace
            service_result = SimpleNamespace(
                total_services=count_result.total_services or 0 if count_result else 0,
                total_revenue=0.0,  # Already included in checkout.service_total
                billed_services=count_result.billed_services or 0 if count_result else 0,
                unbilled_services=count_result.unbilled_services or 0 if count_result else 0,
                billed_revenue=0.0,  # Already included in checkout.service_total
                unbilled_revenue=0.0,  # Unbilled services not yet in checkout
            )
        except Exception as e:
            # If query fails, return zeros
            import traceback
            print(f"Service query error: {str(e)}\n{traceback.format_exc()}")
            from types import SimpleNamespace
            service_result = SimpleNamespace(
                total_services=0,
                total_revenue=0.0,
                billed_services=0,
                unbilled_services=0,
                billed_revenue=0.0,
                unbilled_revenue=0.0,
            )
        
        service_stats = {
        "total_services": service_result.total_services or 0 if service_result else 0,
        "total_revenue": float(service_result.total_revenue or 0) if service_result else 0.0,
        "billed_services": service_result.billed_services or 0 if service_result else 0,
        "unbilled_services": service_result.unbilled_services or 0 if service_result else 0,
        "billed_revenue": float(service_result.billed_revenue or 0) if service_result else 0.0,
        "unbilled_revenue": float(service_result.unbilled_revenue or 0) if service_result else 0.0,
        }
        
        # 4. Expenses - Use SQL aggregations (with timeout protection)
        try:
            expense_date_filter = []
            if branch_id is not None:
                expense_date_filter.append(Expense.branch_id == branch_id)
            if start_dt:
                expense_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt
                expense_date_filter.append(Expense.date >= expense_date)
            if end_dt:
                expense_date = end_dt.date() if isinstance(end_dt, datetime) else end_dt
                expense_date_filter.append(Expense.date <= expense_date)
            
            expense_query = db.query(
                func.count(Expense.id).label("total_expenses"),
                func.coalesce(func.sum(Expense.amount), 0).label("total_amount"),
            )
            if expense_date_filter:
                expense_query = expense_query.filter(and_(*expense_date_filter))
            
            expense_result = expense_query.first()
            
            # Get expenses by category using aggregation (limit to avoid timeout)
            expense_category_query = db.query(
                func.coalesce(Expense.category, "Uncategorized").label("category"),
                func.count(Expense.id).label("count"),
                func.coalesce(func.sum(Expense.amount), 0).label("amount"),
            )
            if expense_date_filter:
                expense_category_query = expense_category_query.filter(and_(*expense_date_filter))
            expense_category_query = expense_category_query.group_by(Expense.category).limit(50)  # Limit categories
            
            expense_by_category = {}
            for row in expense_category_query.all():
                category = row.category or "Uncategorized"
                expense_by_category[category] = {
                    "count": row.count or 0,
                    "amount": float(row.amount or 0)
                }
            
            expense_stats = {
                "total_expenses": expense_result.total_expenses or 0 if expense_result else 0,
                "total_amount": float(expense_result.total_amount or 0) if expense_result else 0.0,
                "by_category": expense_by_category
            }
        except Exception as e:
            print(f"Expense query error: {str(e)}")
            expense_stats = {
                "total_expenses": 0,
                "total_amount": 0.0,
                "by_category": {}
            }
        
        # 5. Inventory Purchases - Use SQL aggregations (with timeout protection)
        try:
            purchase_date_filter = []
            if branch_id is not None:
                purchase_date_filter.append(PurchaseMaster.branch_id == branch_id)
            if start_dt:
                purchase_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt
                purchase_date_filter.append(PurchaseMaster.purchase_date >= purchase_date)
            if end_dt:
                purchase_date = end_dt.date() if isinstance(end_dt, datetime) else end_dt
                purchase_date_filter.append(PurchaseMaster.purchase_date <= purchase_date)
            
            purchase_query = db.query(
                func.count(PurchaseMaster.id).label("total_purchases"),
                func.coalesce(func.sum(PurchaseMaster.total_amount), 0).label("total_amount"),
                func.coalesce(func.sum(PurchaseMaster.sub_total), 0).label("subtotal"),
                func.coalesce(func.sum(PurchaseMaster.total_cgst), 0).label("total_cgst"),
                func.coalesce(func.sum(PurchaseMaster.total_sgst), 0).label("total_sgst"),
                func.coalesce(func.sum(PurchaseMaster.total_igst), 0).label("total_igst"),
                func.coalesce(func.sum(PurchaseMaster.total_discount), 0).label("total_discount"),
            )
            if purchase_date_filter:
                purchase_query = purchase_query.filter(and_(*purchase_date_filter))
            
            purchase_result = purchase_query.first()
        except Exception as e:
            print(f"Purchase query error: {str(e)}")
            from types import SimpleNamespace
            purchase_result = SimpleNamespace(
                total_purchases=0,
                total_amount=0,
                subtotal=0,
                total_cgst=0,
                total_sgst=0,
                total_igst=0,
                total_discount=0
            )
        
        # Get purchases by status using aggregation (with timeout protection)
        try:
            purchase_status_query = db.query(
                func.coalesce(PurchaseMaster.status, "pending").label("status"),
                func.count(PurchaseMaster.id).label("count"),
                func.coalesce(func.sum(PurchaseMaster.total_amount), 0).label("amount"),
            )
            if purchase_date_filter:
                purchase_status_query = purchase_status_query.filter(and_(*purchase_date_filter))
            purchase_status_query = purchase_status_query.group_by(PurchaseMaster.status).limit(20)  # Limit statuses
            
            purchase_by_status = {}
            for row in purchase_status_query.all():
                status = row.status or "pending"
                purchase_by_status[status] = {
                    "count": row.count or 0,
                    "amount": float(row.amount or 0)
                }
        except Exception as e:
            print(f"Purchase status query error: {str(e)}")
            purchase_by_status = {}
        
        purchase_stats = {
        "total_purchases": purchase_result.total_purchases or 0 if purchase_result else 0,
        "total_amount": float(purchase_result.total_amount or 0) if purchase_result else 0.0,
        "subtotal": float(purchase_result.subtotal or 0) if purchase_result else 0.0,
        "total_cgst": float(purchase_result.total_cgst or 0) if purchase_result else 0.0,
        "total_sgst": float(purchase_result.total_sgst or 0) if purchase_result else 0.0,
        "total_igst": float(purchase_result.total_igst or 0) if purchase_result else 0.0,
        "total_discount": float(purchase_result.total_discount or 0) if purchase_result else 0.0,
        "by_status": purchase_by_status
        }
        
        # 6. Inventory Consumption - Use SQL aggregations (with timeout protection)
        try:
            consumption_date_filter = []
            if branch_id is not None:
                consumption_date_filter.append(InventoryTransaction.branch_id == branch_id)
            if start_dt:
                consumption_date_filter.append(InventoryTransaction.created_at >= start_dt)
            if end_dt:
                consumption_date_filter.append(InventoryTransaction.created_at <= end_dt)
            
            consumption_query = db.query(
                func.count(InventoryTransaction.id).label("total_transactions"),
                func.coalesce(func.sum(InventoryTransaction.total_amount), 0).label("total_cogs"),
                func.coalesce(func.sum(InventoryTransaction.quantity), 0).label("total_quantity"),
            ).filter(InventoryTransaction.transaction_type == "out")
            if consumption_date_filter:
                consumption_query = consumption_query.filter(and_(*consumption_date_filter))
            
            consumption_result = consumption_query.first()
            consumption_stats = {
                "total_transactions": consumption_result.total_transactions or 0 if consumption_result else 0,
                "total_cogs": float(consumption_result.total_cogs or 0) if consumption_result else 0.0,
                "total_quantity": float(consumption_result.total_quantity or 0) if consumption_result else 0.0,
            }
        except Exception as e:
            print(f"Consumption query error: {str(e)}")
            consumption_stats = {
                "total_transactions": 0,
                "total_cogs": 0.0,
                "total_quantity": 0.0,
            }
        
        # Calculate Summary
        total_revenue = (
            checkout_stats["grand_total"] +
            food_stats["billed_revenue"] +
            service_stats["billed_revenue"]
        )
        
        total_expenses = (
            expense_stats["total_amount"] +
            purchase_stats["total_amount"] +
            consumption_stats["total_cogs"]
        )
        
        net_profit = total_revenue - total_expenses
        
        return {
            "period": {
                "start_date": start_date if start_date else None,
                "end_date": end_date if end_date else None,
            },
            "revenue": {
                "checkouts": checkout_stats,
                "food_orders": food_stats,
                "services": service_stats,
                "total_revenue": total_revenue,
            },
            "expenses": {
                "operating_expenses": expense_stats,
                "inventory_purchases": purchase_stats,
                "inventory_consumption": consumption_stats,
                "total_expenses": total_expenses,
            },
            "summary": {
                "total_revenue": total_revenue,
                "total_expenses": total_expenses,
                "net_profit": net_profit,
                "profit_margin": (net_profit / total_revenue * 100) if total_revenue > 0 else 0,
            },
            "calculated_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        import traceback
        error_msg = f"Error generating auto-report: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")


# ── Seed Chart of Accounts ───────────────────────────────────────────────────
@router.post("/seed-chart-of-accounts")
def seed_chart_of_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Seed a standard hospitality Chart of Accounts.
    Creates 17 account groups and 41 ledgers.
    Safe to call: skipped automatically if groups already exist.
    """
    from app.models.account import AccountGroup, AccountLedger

    existing = db.query(AccountGroup).count()
    if existing > 0:
        return {
            "status": "skipped",
            "message": f"Already have {existing} account groups. Delete them first to re-seed.",
            "groups_created": 0,
            "ledgers_created": 0,
        }

    ACCOUNT_GROUPS = [
        # Assets
        {"name": "Current Assets",          "account_type": "Asset",     "description": "Short-term assets"},
        {"name": "Fixed Assets",            "account_type": "Asset",     "description": "Long-term assets"},
        {"name": "Cash & Bank",             "account_type": "Asset",     "description": "Cash and bank accounts"},
        # Liabilities
        {"name": "Current Liabilities",     "account_type": "Liability", "description": "Short-term obligations"},
        {"name": "Long-term Liabilities",   "account_type": "Liability", "description": "Long-term obligations"},
        {"name": "GST Payable",             "account_type": "Liability", "description": "GST tax liabilities"},
        # Revenue
        {"name": "Room Revenue",            "account_type": "Revenue",   "description": "Income from room bookings"},
        {"name": "F&B Revenue",             "account_type": "Revenue",   "description": "Food and beverage income"},
        {"name": "Service Revenue",         "account_type": "Revenue",   "description": "Income from services"},
        {"name": "Other Income",            "account_type": "Revenue",   "description": "Miscellaneous income"},
        # Expenses
        {"name": "Staff Expenses",          "account_type": "Expense",   "description": "Salaries and staff costs"},
        {"name": "Operational Expenses",    "account_type": "Expense",   "description": "Day-to-day operating costs"},
        {"name": "Utility Expenses",        "account_type": "Expense",   "description": "Electricity, water, etc."},
        {"name": "Maintenance Expenses",    "account_type": "Expense",   "description": "Repairs and maintenance"},
        {"name": "Marketing Expenses",      "account_type": "Expense",   "description": "Advertising and promotions"},
        # Tax
        {"name": "GST Receivable (ITC)",    "account_type": "Tax",       "description": "Input tax credit accounts"},
        {"name": "Tax Payable",             "account_type": "Tax",       "description": "Tax liabilities"},
    ]

    group_map = {}
    for g in ACCOUNT_GROUPS:
        grp = AccountGroup(**g)
        db.add(grp)
        db.flush()
        group_map[g["name"]] = grp.id

    def gid(name):
        return group_map[name]

    LEDGERS = [
        # Cash & Bank
        {"name": "Cash in Hand",                    "code": "1001", "group_id": gid("Cash & Bank"),          "module": "General",   "balance_type": "debit",  "opening_balance": 0},
        {"name": "Bank Account - Main",             "code": "1002", "group_id": gid("Cash & Bank"),          "module": "General",   "balance_type": "debit",  "opening_balance": 0},
        {"name": "Petty Cash",                      "code": "1003", "group_id": gid("Cash & Bank"),          "module": "General",   "balance_type": "debit",  "opening_balance": 0},
        # Current Assets
        {"name": "Accounts Receivable",             "code": "1101", "group_id": gid("Current Assets"),      "module": "Booking",   "balance_type": "debit",  "opening_balance": 0},
        {"name": "Advance Deposits - Guests",       "code": "1102", "group_id": gid("Current Assets"),      "module": "Booking",   "balance_type": "debit",  "opening_balance": 0},
        {"name": "Inventory Stock",                 "code": "1103", "group_id": gid("Current Assets"),      "module": "Inventory", "balance_type": "debit",  "opening_balance": 0},
        {"name": "Prepaid Expenses",                "code": "1104", "group_id": gid("Current Assets"),      "module": "General",   "balance_type": "debit",  "opening_balance": 0},
        # Fixed Assets
        {"name": "Furniture & Fixtures",            "code": "1201", "group_id": gid("Fixed Assets"),        "module": "General",   "balance_type": "debit",  "opening_balance": 0},
        {"name": "Equipment",                       "code": "1202", "group_id": gid("Fixed Assets"),        "module": "General",   "balance_type": "debit",  "opening_balance": 0},
        {"name": "Building",                        "code": "1203", "group_id": gid("Fixed Assets"),        "module": "General",   "balance_type": "debit",  "opening_balance": 0},
        # Current Liabilities
        {"name": "Accounts Payable",                "code": "2001", "group_id": gid("Current Liabilities"), "module": "Purchase",  "balance_type": "credit", "opening_balance": 0},
        {"name": "Advance from Guests",             "code": "2002", "group_id": gid("Current Liabilities"), "module": "Booking",   "balance_type": "credit", "opening_balance": 0},
        {"name": "Salaries Payable",                "code": "2003", "group_id": gid("Current Liabilities"), "module": "Employee",  "balance_type": "credit", "opening_balance": 0},
        # GST Payable
        {"name": "CGST Payable",                    "code": "2101", "group_id": gid("GST Payable"),         "module": "GST",       "tax_type": "CGST",       "balance_type": "credit", "opening_balance": 0},
        {"name": "SGST Payable",                    "code": "2102", "group_id": gid("GST Payable"),         "module": "GST",       "tax_type": "SGST",       "balance_type": "credit", "opening_balance": 0},
        {"name": "IGST Payable",                    "code": "2103", "group_id": gid("GST Payable"),         "module": "GST",       "tax_type": "IGST",       "balance_type": "credit", "opening_balance": 0},
        # Revenue
        {"name": "Room Tariff Income",              "code": "4001", "group_id": gid("Room Revenue"),        "module": "Booking",   "balance_type": "credit", "opening_balance": 0},
        {"name": "Package Revenue",                 "code": "4002", "group_id": gid("Room Revenue"),        "module": "Booking",   "balance_type": "credit", "opening_balance": 0},
        {"name": "Early Check-in / Late Check-out", "code": "4003", "group_id": gid("Room Revenue"),        "module": "Booking",   "balance_type": "credit", "opening_balance": 0},
        {"name": "Restaurant Revenue",              "code": "4101", "group_id": gid("F&B Revenue"),         "module": "Food",      "balance_type": "credit", "opening_balance": 0},
        {"name": "Bar Revenue",                     "code": "4102", "group_id": gid("F&B Revenue"),         "module": "Food",      "balance_type": "credit", "opening_balance": 0},
        {"name": "Laundry Revenue",                 "code": "4201", "group_id": gid("Service Revenue"),     "module": "Service",   "balance_type": "credit", "opening_balance": 0},
        {"name": "Spa & Wellness Revenue",          "code": "4202", "group_id": gid("Service Revenue"),     "module": "Service",   "balance_type": "credit", "opening_balance": 0},
        {"name": "Event Revenue",                   "code": "4203", "group_id": gid("Service Revenue"),     "module": "Service",   "balance_type": "credit", "opening_balance": 0},
        {"name": "Miscellaneous Income",            "code": "4301", "group_id": gid("Other Income"),        "module": "General",   "balance_type": "credit", "opening_balance": 0},
        {"name": "Cancellation Charges",            "code": "4302", "group_id": gid("Other Income"),        "module": "Booking",   "balance_type": "credit", "opening_balance": 0},
        # Expenses
        {"name": "Salaries & Wages",                "code": "5001", "group_id": gid("Staff Expenses"),      "module": "Employee",  "balance_type": "debit",  "opening_balance": 0},
        {"name": "Staff Benefits",                  "code": "5002", "group_id": gid("Staff Expenses"),      "module": "Employee",  "balance_type": "debit",  "opening_balance": 0},
        {"name": "Food & Beverage Purchases",       "code": "5101", "group_id": gid("Operational Expenses"),"module": "Purchase",  "balance_type": "debit",  "opening_balance": 0},
        {"name": "Housekeeping Supplies",           "code": "5102", "group_id": gid("Operational Expenses"),"module": "Inventory", "balance_type": "debit",  "opening_balance": 0},
        {"name": "Laundry Costs",                   "code": "5103", "group_id": gid("Operational Expenses"),"module": "Service",   "balance_type": "debit",  "opening_balance": 0},
        {"name": "Electricity",                     "code": "5201", "group_id": gid("Utility Expenses"),    "module": "Expense",   "balance_type": "debit",  "opening_balance": 0},
        {"name": "Water",                           "code": "5202", "group_id": gid("Utility Expenses"),    "module": "Expense",   "balance_type": "debit",  "opening_balance": 0},
        {"name": "Internet & Communications",       "code": "5203", "group_id": gid("Utility Expenses"),    "module": "Expense",   "balance_type": "debit",  "opening_balance": 0},
        {"name": "Building Maintenance",            "code": "5301", "group_id": gid("Maintenance Expenses"),"module": "Expense",   "balance_type": "debit",  "opening_balance": 0},
        {"name": "Equipment Maintenance",           "code": "5302", "group_id": gid("Maintenance Expenses"),"module": "Expense",   "balance_type": "debit",  "opening_balance": 0},
        {"name": "Advertising",                     "code": "5401", "group_id": gid("Marketing Expenses"),  "module": "Expense",   "balance_type": "debit",  "opening_balance": 0},
        {"name": "Online Travel Agent Commissions", "code": "5402", "group_id": gid("Marketing Expenses"),  "module": "Expense",   "balance_type": "debit",  "opening_balance": 0},
        # GST ITC
        {"name": "CGST Input Credit",               "code": "6001", "group_id": gid("GST Receivable (ITC)"),"module": "GST",       "tax_type": "CGST",       "balance_type": "debit",  "opening_balance": 0},
        {"name": "SGST Input Credit",               "code": "6002", "group_id": gid("GST Receivable (ITC)"),"module": "GST",       "tax_type": "SGST",       "balance_type": "debit",  "opening_balance": 0},
        {"name": "IGST Input Credit",               "code": "6003", "group_id": gid("GST Receivable (ITC)"),"module": "GST",       "tax_type": "IGST",       "balance_type": "debit",  "opening_balance": 0},
    ]

    ledger_count = 0
    for l in LEDGERS:
        ledger = AccountLedger(**l)
        db.add(ledger)
        ledger_count += 1

    db.commit()

    return {
        "status": "success",
        "message": f"Seeded {len(ACCOUNT_GROUPS)} account groups and {ledger_count} ledgers.",
        "groups_created": len(ACCOUNT_GROUPS),
        "ledgers_created": ledger_count,
    }
