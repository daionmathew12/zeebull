from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.foodorder import FoodOrderCreate, FoodOrderOut, FoodOrderUpdate
from app.curd import foodorder as crud  # ✅ Correct import
from app.utils.auth import get_db, get_current_user
from app.utils.branch_scope import get_branch_id
from app.models.user import User

from app.utils.api_optimization import optimize_limit, MAX_LIMIT_LOW_NETWORK
from typing import List

router = APIRouter(prefix="/food-orders", tags=["Food Orders"])

def _create_order_impl(order: FoodOrderCreate, db: Session, current_user: User):
    """Helper function for create_order"""
    return crud.create_food_order(db, order)

def create_order(
    order: FoodOrderCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):
    return crud.create_food_order(db, order, branch_id=branch_id)


@router.post("/", response_model=FoodOrderOut)  # Handle trailing slash
def create_order_slash(
    order: FoodOrderCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):
    return crud.create_food_order(db, order, branch_id=branch_id)


def _get_orders_impl(db: Session, skip: int = 0, limit: int = 20, room_id: int = None, booking_id: int = None, package_booking_id: int = None, user_id: int = None):
    """Helper function for get_orders - optimized for low network"""
    limit = optimize_limit(limit, MAX_LIMIT_LOW_NETWORK)
    return crud.get_food_orders(db, skip=skip, limit=limit, room_id=room_id, booking_id=booking_id, package_booking_id=package_booking_id, user_id=user_id)

def trigger_scheduled_orders(db: Session):
    """Check for scheduled orders and trigger them if due."""
    return crud.trigger_scheduled_orders(db)

@router.get("", response_model=List[FoodOrderOut])
def get_orders(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user), 
    branch_id: int = Depends(get_branch_id),
    skip: int = 0, 
    limit: int = 20, 
    room_id: int = None, 
    booking_id: int = None, 
    package_booking_id: int = None, 
    user_id: int = None
):
    crud.trigger_scheduled_orders(db, branch_id=branch_id)
    limit = optimize_limit(limit, MAX_LIMIT_LOW_NETWORK)
    orders = crud.get_food_orders(db, branch_id=branch_id, skip=skip, limit=limit, room_id=room_id, booking_id=booking_id, package_booking_id=package_booking_id, user_id=user_id)
    if orders:
        print(f"[DEBUG-API] Order #{orders[0].id} items: {[(i.food_item_name, getattr(i, 'price', 'N/A'), getattr(i, 'subtotal', 'N/A')) for i in orders[0].items]}")
    return orders


@router.get("/", response_model=List[FoodOrderOut])  # Handle trailing slash
def get_orders_slash(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user), 
    branch_id: int = Depends(get_branch_id),
    skip: int = 0, 
    limit: int = 20, 
    room_id: int = None, 
    booking_id: int = None, 
    package_booking_id: int = None, 
    user_id: int = None
):
    crud.trigger_scheduled_orders(db, branch_id=branch_id)
    limit = optimize_limit(limit, MAX_LIMIT_LOW_NETWORK)
    return crud.get_food_orders(db, branch_id=branch_id, skip=skip, limit=limit, room_id=room_id, booking_id=booking_id, package_booking_id=package_booking_id, user_id=user_id)


@router.delete("/{order_id}")
def delete_order(
    order_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):
    deleted = crud.delete_food_order(db, order_id, branch_id=branch_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Deleted successfully"}


@router.patch("/{order_id}/cancel")
def cancel_order(
    order_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):
    order = crud.update_food_order_status(db, order_id, status="cancelled", branch_id=branch_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Order cancelled"}


@router.put("/{order_id}", response_model=FoodOrderOut)
def update_order(
    order_id: int, 
    order_update: FoodOrderUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):
    from app.models.foodorder import FoodOrder
    from app.models.employee import Employee
    
    # Check current status before update
    current_order = db.query(FoodOrder).filter(FoodOrder.id == order_id, FoodOrder.branch_id == branch_id).first()

    if not current_order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    # Auto-set prepared_by_id if moving to cooking
    if order_update.status in ['cooking', 'accepted', 'preparing', 'ready'] and current_order.prepared_by_id is None:
        # Link current user (chef) to the order
        chef_emp = db.query(Employee).filter(Employee.user_id == current_user.id, Employee.branch_id == branch_id).first()

        if chef_emp:
            order_update.prepared_by_id = chef_emp.id

    updated = crud.update_food_order(db, order_id, order_update, branch_id=branch_id)     
    return updated


@router.put("/{order_id}/", response_model=FoodOrderOut)  # Handle trailing slash
def update_order_slash(
    order_id: int, 
    order_update: FoodOrderUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):
    return update_order(order_id, order_update, db, current_user, branch_id)


@router.post("/{order_id}/mark-paid")
def mark_order_paid(
    order_id: int,
    payment_method: str,  # "cash", "card", "upi"
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):

    """
    Mark a food order as paid at delivery time.
    Calculates GST (5%) and updates payment details.
    """
    from app.models.foodorder import FoodOrder
    from datetime import timezone, datetime
    
    order = db.query(FoodOrder).filter(FoodOrder.id == order_id, FoodOrder.branch_id == branch_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.billing_status == "paid":
        raise HTTPException(status_code=400, detail="Order already marked as paid")
    
    # Calculate GST (5% for food)
    base_amount = order.amount or 0
    gst_amount = base_amount * 0.05
    total_with_gst = base_amount + gst_amount
    
    # Update order with payment details
    order.billing_status = "paid"
    order.payment_method = payment_method
    order.payment_time = datetime.now(timezone.utc)
    order.gst_amount = gst_amount
    order.total_with_gst = total_with_gst
    
    db.commit()
    db.refresh(order)
    
    # Automatically create journal entry for food revenue
    try:
        from app.utils.accounting_helpers import create_food_order_journal_entry
        
        # Determine room number if available
        room_number = "Unknown"
        if order.room_id:
            from app.models.room import Room
            room = db.query(Room).filter(Room.id == order.room_id, Room.branch_id == branch_id).first()

            if room:
                room_number = room.number
        
        create_food_order_journal_entry(
            db=db,
            food_order_id=order.id,
            amount=total_with_gst,
            room_number=room_number,
            gst_rate=5.0,
            branch_id=branch_id,
            created_by=current_user.id
        )

    except Exception as e:
        # Log error but don't fail the request
        import traceback
        print(f"Failed to create journal entry for food order {order.id}: {str(e)}")
        print(traceback.format_exc())

    return {
        "message": "Order marked as paid successfully",
        "order_id": order.id,
        "payment_method": payment_method,
        "base_amount": base_amount,
        "gst_amount": gst_amount,
        "total_with_gst": total_with_gst,
        "payment_time": order.payment_time
    }
