from sqlalchemy.orm import Session
from app.models.foodorder import FoodOrder, FoodOrderItem
from app.models.booking import Booking, BookingRoom
from app.models.Package import PackageBooking, PackageBookingRoom
from app.models.service_request import ServiceRequest
from app.schemas.foodorder import FoodOrderCreate, FoodOrderUpdate
from datetime import datetime
from app.curd.notification import notify_food_order_created, notify_food_order_status_changed

def get_guest_for_room(room_id, db: Session, reference_date=None):
    """Get guest name for a room from either regular or package bookings"""
    if not room_id:
        return None
    
    # Ensure reference_date is a date object for comparison with Date columns
    ref_date = reference_date.date() if reference_date and isinstance(reference_date, datetime) else reference_date
    
    # Check regular bookings first
    query = (
        db.query(Booking)
        .join(BookingRoom)
        .filter(BookingRoom.room_id == room_id)
    )
    
    if ref_date:
        # Find booking covering the reference date
        query = query.filter(Booking.check_in <= ref_date)\
                     .filter(Booking.check_out >= ref_date)\
                     .filter(Booking.status != "cancelled")
    else:
        # Check active bookings
        query = query.filter(Booking.status.in_(["checked-in", "booked"]))
        
    active_booking = query.order_by(Booking.id.desc()).first()
    
    if active_booking:
        return active_booking.guest_name
    
    # Check package bookings
    pkg_query = (
        db.query(PackageBooking)
        .join(PackageBookingRoom)
        .filter(PackageBookingRoom.room_id == room_id)
    )
    
    if ref_date:
        pkg_query = pkg_query.filter(PackageBooking.check_in <= ref_date)\
                             .filter(PackageBooking.check_out >= ref_date)\
                             .filter(PackageBooking.status != "cancelled")
    else:
        pkg_query = pkg_query.filter(PackageBooking.status.in_(["checked-in", "booked"]))
        
    active_package_booking = pkg_query.order_by(PackageBooking.id.desc()).first()
    
    if active_package_booking:
        return active_package_booking.guest_name
    
    return None

def create_food_order(db: Session, order_data: FoodOrderCreate):
    order = FoodOrder(
        room_id=order_data.room_id,
        amount=order_data.amount,
        assigned_employee_id=order_data.assigned_employee_id,
        status="pending",
        billing_status="unbilled",
        order_type=getattr(order_data, 'order_type', 'dine_in'),
        delivery_request=getattr(order_data, 'delivery_request', None),
        created_by_id=order_data.assigned_employee_id # Default creator to assigned employee for now
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    for item_data in order_data.items:
        item = FoodOrderItem(
            order_id=order.id,
            food_item_id=item_data.food_item_id,
            quantity=item_data.quantity,
        )
        db.add(item)
    db.commit()
    db.refresh(order)
    
    # Create service request immediately for room service orders
    if order.order_type == "room_service":
        # Check if service request already exists
        existing_request = db.query(ServiceRequest).filter(
            ServiceRequest.food_order_id == order.id
        ).first()
        if not existing_request:
            service_request = ServiceRequest(
                food_order_id=order.id,
                room_id=order.room_id,
                employee_id=order.assigned_employee_id,
                request_type="delivery",
                description=order.delivery_request or f"Room service delivery for food order #{order.id}",
                status="pending"
            )
            db.add(service_request)
            db.commit()
    
    
    # Notify about new order
    try:
        from app.models.room import Room
        room = db.query(Room).filter(Room.id == order.room_id).first()
        room_number = room.number if room else "Unknown"
        notify_food_order_created(db, room_number, order.id)
    except Exception as e:
        print(f"Notification error: {e}")
    
    
    # Reload order with relationships to ensure response has all data (especially food_item_name)
    from sqlalchemy.orm import joinedload
    order = (
        db.query(FoodOrder)
        .options(
            joinedload(FoodOrder.items).joinedload(FoodOrderItem.food_item)
        )
        .filter(FoodOrder.id == order.id)
        .first()
    )

    return order

def get_food_orders(db: Session, skip: int = 0, limit: int = 100):
    from sqlalchemy.orm import joinedload
    
    # Cap limit to prevent performance issues
    if limit > 200:
        limit = 200
    if limit < 1:
        limit = 20
    
    # Eager load relationships so guest/employee names are available
    try:
        orders = (
            db.query(FoodOrder)
            .options(
                joinedload(FoodOrder.employee),  # Load employee for employee name
                joinedload(FoodOrder.creator),   # Load creator name
                joinedload(FoodOrder.chef),      # Load chef name
                joinedload(FoodOrder.room),      # Load room for room number
                joinedload(FoodOrder.items).joinedload(FoodOrderItem.food_item)  # Load items and food details
            )
            .order_by(FoodOrder.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        # Populate computed fields
        for order in orders:
            # Set employee name
            if order.employee:
                order.employee_name = order.employee.name
            else:
                order.employee_name = None
            
            # Set room number
            if order.room:
                order.room_number = order.room.number
            else:
                order.room_number = None
            
            # Set additional names
            order.creator_name = order.creator.name if order.creator else "Unknown"
            order.chef_name = order.chef.name if order.chef else "Not Started"
            
            # Set guest name significantly improved logic:
            # Search for booking that was active at the time the order was created
            order.guest_name = get_guest_for_room(order.room_id, db, order.created_at)
        
        return orders
    except Exception as e:
        print(f"[ERROR] Error in get_food_orders: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def delete_food_order(db: Session, order_id: int):
    order = db.query(FoodOrder).filter(FoodOrder.id == order_id).first()
    if order:
        db.delete(order)
        db.commit()
    return order

def update_food_order_status(db: Session, order_id: int, status: str):
    order = db.query(FoodOrder).filter(FoodOrder.id == order_id).first()
    if order:
        old_status = order.status
        order.status = status
        
        # If moving to cooking/preparing, set the chef
        # (This usually happens via the kitchen staff's UI)
        # Note: We don't have the context of 'current_user' here, 
        # but the caller (API) can pass prepared_by_id if needed.
        
        db.commit()
        db.refresh(order)
        
        # Process inventory usage if completed
        if old_status != "completed" and status == "completed":
            try:
                from app.curd.inventory import process_food_order_usage
                process_food_order_usage(db, order.id)
                db.commit()
            except Exception as e:
                db.rollback()
                print(f"Failed to process inventory usage: {e}")
        
        # Notify status change
        try:
            from app.models.room import Room
            from app.models.employee import Employee
            
            room = db.query(Room).filter(Room.id == order.room_id).first()
            room_number = room.number if room else "Unknown"
            
            recipient_id = None
            if order.assigned_employee_id:
                emp = db.query(Employee).filter(Employee.id == order.assigned_employee_id).first()
                if emp:
                    recipient_id = emp.user_id
            
            notify_food_order_status_changed(db, room_number, status, order.id, recipient_id=recipient_id)
        except Exception as e:
            print(f"Notification error: {e}")
            
    return order

def update_food_order(db: Session, order_id: int, update_data: FoodOrderUpdate):
    order = db.query(FoodOrder).filter(FoodOrder.id == order_id).first()
    if not order:
        return None

    if update_data.room_id is not None:
        order.room_id = update_data.room_id
    if update_data.amount is not None:
        order.amount = update_data.amount
    if update_data.assigned_employee_id is not None:
        order.assigned_employee_id = update_data.assigned_employee_id
    if update_data.status is not None:
        old_status = order.status
        order.status = update_data.status
        
        # If status moved to cooking/preparing, and prepared_by_id not set, 
        # we can assume the person updating it is preparing it? 
        # Actually, let's check if prepared_by_id is explicitly passed.
        if update_data.prepared_by_id is not None:
            order.prepared_by_id = update_data.prepared_by_id
        elif update_data.status in ['cooking', 'accepted', 'preparing'] and order.prepared_by_id is None:
             # If the UI doesn't pass it, we might set it in the endpoint layer
             pass
        
        # Process inventory usage if completed
        if old_status != "completed" and update_data.status == "completed":
            try:
                from app.curd.inventory import process_food_order_usage
                process_food_order_usage(db, order.id)
            except Exception as e:
                print(f"Failed to process inventory usage: {e}")

        # If completing a room service order, create a service request
        if update_data.status == "completed" and order.order_type == "room_service":
            # Check if service request already exists
            existing_request = db.query(ServiceRequest).filter(
                ServiceRequest.food_order_id == order.id
            ).first()
            if not existing_request:
                service_request = ServiceRequest(
                    food_order_id=order.id,
                    room_id=order.room_id,
                    employee_id=order.assigned_employee_id,
                    request_type="delivery",
                    description=order.delivery_request or f"Room service delivery for food order #{order.id}",
                    status="pending"
                )
                db.add(service_request)
        
        # Notify status change
        try:
            from app.models.room import Room
            from app.models.employee import Employee
            
            room = db.query(Room).filter(Room.id == order.room_id).first()
            room_number = room.number if room else "Unknown"
            
            recipient_id = None
            if order.assigned_employee_id:
                emp = db.query(Employee).filter(Employee.id == order.assigned_employee_id).first()
                if emp:
                    recipient_id = emp.user_id

            notify_food_order_status_changed(db, room_number, update_data.status, order.id, recipient_id=recipient_id)
        except Exception as e:
            print(f"Notification error: {e}")

    if update_data.billing_status is not None:
        order.billing_status = update_data.billing_status
    if update_data.payment_method is not None:
        order.payment_method = update_data.payment_method
    if update_data.order_type is not None:
        order.order_type = update_data.order_type
    if update_data.delivery_request is not None:
        order.delivery_request = update_data.delivery_request

    if update_data.items is not None:
        db.query(FoodOrderItem).filter(FoodOrderItem.order_id == order.id).delete()
        for item_data in update_data.items:
            item = FoodOrderItem(
                order_id=order.id,
                food_item_id=item_data.food_item_id,
                quantity=item_data.quantity,
            )
            db.add(item)

    db.commit()
    db.refresh(order)
    return order
