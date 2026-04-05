from sqlalchemy.orm import Session
from app.models.foodorder import FoodOrder, FoodOrderItem
from app.models.booking import Booking, BookingRoom
from app.models.Package import PackageBooking, PackageBookingRoom
from app.models.service_request import ServiceRequest
from app.schemas.foodorder import FoodOrderCreate, FoodOrderUpdate
from datetime import datetime, timedelta
import re
from app.curd.notification import notify_food_order_created, notify_food_order_status_changed

def get_ist_now():
    """Get current time in Indian Standard Time (UTC+5:30)"""
    return datetime.utcnow() + timedelta(hours=5, minutes=30)

def get_booking_for_room(room_id, db: Session, branch_id: int, reference_date=None) -> tuple:
    """Get active booking for a room from either regular or package bookings within a branch"""

    if not room_id:
        return None, False
    
    # Ensure reference_date is a datetime or date object (defaults to IST Now)
    ref_dt = reference_date if reference_date else get_ist_now()
    ref_date = ref_dt.date() if isinstance(ref_dt, datetime) else ref_dt
    
    # 1. Check regular bookings (Primary Selection: include date overlap AND active status)
    active_booking = (
        db.query(Booking)
        .join(BookingRoom)
        .filter(BookingRoom.room_id == room_id, Booking.branch_id == branch_id)
        .filter(Booking.status.in_(["booked", "checked-in", "checked_in"]))
        .filter(Booking.check_in <= ref_date)
        .filter(Booking.check_out >= ref_date)
        .order_by(Booking.id.desc()).first()
    )
    
    if active_booking:
        return active_booking.id, False
    
    # 2. Check package bookings (Primary Selection: include date overlap AND active status)
    active_package_booking = (
        db.query(PackageBooking)
        .join(PackageBookingRoom)
        .filter(PackageBookingRoom.room_id == room_id, PackageBooking.branch_id == branch_id)
        .filter(PackageBooking.status.in_(["booked", "checked-in", "checked_in"]))
        .filter(PackageBooking.check_in <= ref_date)
        .filter(PackageBooking.check_out >= ref_date)
        .order_by(PackageBooking.id.desc()).first()
    )
    
    if active_package_booking:
        return active_package_booking.id, True
    
    # Fallback: Just find ANY active booking (checked-in) for this room if date check was too strict
    fallback = db.query(Booking).join(BookingRoom).filter(
        BookingRoom.room_id == room_id,
        Booking.status.in_(["checked-in", "checked_in"]),
        Booking.branch_id == branch_id
    ).order_by(Booking.id.desc()).first()

    if fallback: return fallback.id, False
    
    fallback_pkg = db.query(PackageBooking).join(PackageBookingRoom).filter(
        PackageBookingRoom.room_id == room_id,
        PackageBooking.status.in_(["checked-in", "checked_in"]),
        PackageBooking.branch_id == branch_id
    ).order_by(PackageBooking.id.desc()).first()

    if fallback_pkg: return fallback_pkg.id, True
    
    return None, False

def get_guest_for_room(room_id, db: Session, branch_id: int, reference_date=None):
    """Get guest name for a room within a specific branch"""
    if not room_id:
        return None
    
    # Ensure reference_date is a date object for comparison with Date columns
    ref_date = reference_date.date() if reference_date and isinstance(reference_date, datetime) else reference_date
    
    # Check regular bookings first
    query = (
        db.query(Booking)
        .join(BookingRoom)
        .filter(BookingRoom.room_id == room_id, Booking.branch_id == branch_id)
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
        .filter(PackageBookingRoom.room_id == room_id, PackageBooking.branch_id == branch_id)
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
    
    # Fallback: Just find ANY active booking for this room if date filter was too strict
    if ref_date:
        fallback = db.query(Booking).join(BookingRoom).filter(
            BookingRoom.room_id == room_id,
            Booking.status.in_(["checked-in", "booked"]),
            Booking.branch_id == branch_id
        ).order_by(Booking.id.desc()).first()
        if fallback: return fallback.guest_name
        
        fallback_pkg = db.query(PackageBooking).join(PackageBookingRoom).filter(
            PackageBookingRoom.room_id == room_id,
            PackageBooking.status.in_(["checked-in", "booked"]),
            PackageBooking.branch_id == branch_id
        ).order_by(PackageBooking.id.desc()).first()
        if fallback_pkg: return fallback_pkg.guest_name

    
    return None

def create_food_order(db: Session, order_data: FoodOrderCreate, branch_id: int):

    status = getattr(order_data, 'status', 'pending')
    billing_status = getattr(order_data, 'billing_status', 'unbilled')
    
    # If amount is 0, it's complimentary - force to room_service
    order_type = getattr(order_data, 'order_type', 'dine_in')
    amount = order_data.amount or 0.0
    if amount == 0:
        order_type = 'room_service'

    # Try to link to a booking if not provided
    booking_id = getattr(order_data, 'booking_id', None)
    package_booking_id = getattr(order_data, 'package_booking_id', None)
    
    if not booking_id and not package_booking_id:
        b_id, is_pkg = get_booking_for_room(order_data.room_id, db, branch_id=branch_id)

        if b_id:
            if is_pkg:
                package_booking_id = b_id
            else:
                booking_id = b_id

    gst_amount = amount * 0.05
    total_with_gst = amount + gst_amount

    order = FoodOrder(
        room_id=order_data.room_id,
        booking_id=booking_id,
        package_booking_id=package_booking_id,
        amount=amount,
        gst_amount=gst_amount,
        total_with_gst=total_with_gst,
        assigned_employee_id=order_data.assigned_employee_id,
        prepared_by_id=order_data.prepared_by_id,
        status=status,
        billing_status=billing_status,
        order_type=order_type,
        delivery_request=getattr(order_data, 'delivery_request', None),
        created_by_id=getattr(order_data, 'created_by_id', None) or order_data.assigned_employee_id,
        created_at=get_ist_now(), # Use IST for consistent creation time
        branch_id=branch_id
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    for item_data in order_data.items:
        item = FoodOrderItem(
            order_id=order.id,
            food_item_id=item_data.food_item_id,
            quantity=item_data.quantity,
            branch_id=branch_id
        )

        db.add(item)
    db.commit()
    db.refresh(order)
    
    # Create service request immediately for room service orders (even if scheduled)
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
                request_type="food_delivery",
                description=order.delivery_request or f"Room service delivery for food order #{order.id}",
                status="pending" if status != "scheduled" else "scheduled",
                branch_id=branch_id
            )

            db.add(service_request)
            db.commit()
    
    
    # Notify about new order
    try:
        from app.models.room import Room
        room = db.query(Room).filter(Room.id == order.room_id, Room.branch_id == branch_id).first()

        room_number = room.number if room else "Unknown"
        notify_food_order_created(db, room_number, order.id, branch_id=branch_id)
    except Exception as e:
        print(f"Notification error: {e}")
    
    
    # Reload order with relationships to ensure response has all data (especially food_item_name)
    from sqlalchemy.orm import joinedload
    order = (
        db.query(FoodOrder)
        .options(
            joinedload(FoodOrder.items).joinedload(FoodOrderItem.food_item)
        )
        .filter(FoodOrder.id == order.id, FoodOrder.branch_id == branch_id)
        .first()

    )

    return order

def get_food_orders(db: Session, branch_id: int, skip: int = 0, limit: int = 100, room_id: int = None, booking_id: int = None, package_booking_id: int = None, user_id: int = None):

    from sqlalchemy.orm import joinedload
    
    # Cap limit to prevent performance issues
    if limit > 200:
        limit = 200
    if limit < 1:
        limit = 20
    
    # Eager load relationships so guest/employee names are available
    try:
        query = db.query(FoodOrder)
        
        if branch_id is not None:
             query = query.filter(FoodOrder.branch_id == branch_id)

        if room_id:
            query = query.filter(FoodOrder.room_id == room_id)
        if booking_id:
            query = query.filter(FoodOrder.booking_id == booking_id)
        if package_booking_id:
            query = query.filter(FoodOrder.package_booking_id == package_booking_id)
        if user_id:
            from sqlalchemy import or_
            query = query.outerjoin(FoodOrder.booking).outerjoin(FoodOrder.package_booking).filter(
                or_(
                    Booking.user_id == user_id,
                    PackageBooking.user_id == user_id
                )
            )
            
        orders = (
            query
            .options(
                joinedload(FoodOrder.employee),  # Load employee for employee name
                joinedload(FoodOrder.creator),   # Load creator name
                joinedload(FoodOrder.chef),      # Load chef name
                joinedload(FoodOrder.room),      # Load room for room number
                joinedload(FoodOrder.booking),   # Load booking for guest name
                joinedload(FoodOrder.package_booking), # Load package booking
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
            if order.booking:
                order.guest_name = order.booking.guest_name
            elif order.package_booking:
                order.guest_name = order.package_booking.guest_name
            else:
                # Fallback: Search for booking that was active at the time the order was created
                order.guest_name = get_guest_for_room(order.room_id, db, branch_id=branch_id, reference_date=order.created_at)

        
        return orders
    except Exception as e:
        print(f"[ERROR] Error in get_food_orders: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def delete_food_order(db: Session, order_id: int, branch_id: int):
    order = db.query(FoodOrder).filter(FoodOrder.id == order_id, FoodOrder.branch_id == branch_id).first()

    if order:
        db.delete(order)
        db.commit()
    return order

def update_food_order_status(db: Session, order_id: int, status: str, branch_id: int):
    order = db.query(FoodOrder).filter(FoodOrder.id == order_id, FoodOrder.branch_id == branch_id).first()

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
        
            try:
                from app.models.room import Room
                from app.models.employee import Employee
                
                room = db.query(Room).filter(Room.id == order.room_id, Room.branch_id == branch_id).first()
                room_number = room.number if room else "Unknown"
                
                recipient_id = None
                if order.assigned_employee_id:
                    emp = db.query(Employee).filter(Employee.id == order.assigned_employee_id, Employee.branch_id == branch_id).first()
                    if emp:
                        recipient_id = emp.user_id
                
                notify_food_order_status_changed(db, room_number, status, order.id, branch_id=branch_id, recipient_id=recipient_id)
            except Exception as e:
                print(f"Notification error: {e}")
            
    return order

def update_food_order(db: Session, order_id: int, update_data: FoodOrderUpdate, branch_id: int):
    query = db.query(FoodOrder).filter(FoodOrder.id == order_id)
    if branch_id is not None:
         query = query.filter(FoodOrder.branch_id == branch_id)
    order = query.first()

    if not order:
        return None

    if update_data.room_id is not None:
        order.room_id = update_data.room_id
    if update_data.amount is not None:
        order.amount = update_data.amount
        order.gst_amount = order.amount * 0.05
        order.total_with_gst = order.amount + order.gst_amount
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

        # Notify status change
        try:
            from app.models.room import Room
            from app.models.employee import Employee
            
            room = db.query(Room).filter(Room.id == order.room_id, Room.branch_id == branch_id).first()
            room_number = room.number if room else "Unknown"
            
            recipient_id = None
            if order.assigned_employee_id:
                emp = db.query(Employee).filter(Employee.id == order.assigned_employee_id, Employee.branch_id == branch_id).first()

                if emp:
                    recipient_id = emp.user_id

            notify_food_order_status_changed(db, room_number, update_data.status, order.id, branch_id=branch_id, recipient_id=recipient_id)
        except Exception as e:
            print(f"Notification error: {e}")

    # Update other fields
    if update_data.billing_status is not None:
        order.billing_status = update_data.billing_status
    if update_data.payment_method is not None:
        order.payment_method = update_data.payment_method
    if update_data.delivery_request is not None:
        order.delivery_request = update_data.delivery_request

    # Force room_service for complimentary orders in update too
    if order.amount == 0:
        order.order_type = "room_service"
    elif update_data.order_type is not None:
        order.order_type = update_data.order_type

    # Ensure ServiceRequest is created for room service orders whenever they are active
    if order.order_type == "room_service" and order.status not in ["cancelled", "deleted"]:
        # Check if service request already exists
        existing_request = db.query(ServiceRequest).filter(
            ServiceRequest.food_order_id == order.id,
            ServiceRequest.branch_id == branch_id
        ).first()

        if not existing_request:
            service_request = ServiceRequest(
                food_order_id=order.id,
                room_id=order.room_id,
                employee_id=order.assigned_employee_id,
                request_type="delivery",
                description=order.delivery_request or f"Room service delivery for food order #{order.id}",
                status="pending" if order.status != "scheduled" else "scheduled",
                branch_id=branch_id
            )
            db.add(service_request)

            print(f"[INFO] Created missing ServiceRequest for room service order {order.id}")

    if update_data.items is not None:
        db.query(FoodOrderItem).filter(FoodOrderItem.order_id == order.id).delete()
        for item_data in update_data.items:
            item = FoodOrderItem(
                order_id=order.id,
                food_item_id=item_data.food_item_id,
                quantity=item_data.quantity,
                branch_id=branch_id
            )
            db.add(item)

    db.commit()
    db.refresh(order)
    return order

def trigger_scheduled_orders(db: Session, branch_id: int):
    """
    Check for scheduled orders and trigger them if within 30 minutes of scheduled time.
    Parses 'delivery_request' to find 'SCHEDULED_FOR: YYYY-MM-DD HH:MM:SS'.
    """
    try:
        from app.models.foodorder import FoodOrder
        from app.models.service_request import ServiceRequest
        
        # Use IST for comparison as scheduled times are usually in IST
        now = get_ist_now()
        
        # Find orders with status 'scheduled'
        query = db.query(FoodOrder).filter(FoodOrder.status == 'scheduled')
        if branch_id is not None:
             query = query.filter(FoodOrder.branch_id == branch_id)
        
        scheduled_orders = query.all()

        
        if scheduled_orders:
            print(f"[DEBUG-TRIGGER] Checking {len(scheduled_orders)} scheduled orders at {now.strftime('%H:%M:%S')}")
        
        triggered_count = 0
        for order in scheduled_orders:
            if not order.delivery_request:
                continue
                
            # Parse scheduled time safely
            # Format: "SCHEDULED_FOR: 2025-12-27 20:00:00 -- ..."
            match = re.search(r"SCHEDULED_FOR: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", order.delivery_request)
            if match:
                time_str = match.group(1)
                try:
                    scheduled_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                    # Use 60 minutes lead time instead of 30 to ensure staff have time to prepare
                    trigger_time = scheduled_time - timedelta(minutes=60)
                    
                    # Debug log for the specific order in the screenshot window
                    if "18:01:00" in time_str or "20:27:00" in time_str:
                         print(f"[DEBUG-TRIGGER] Order {order.id} scheduled for {time_str}. Trigger window starts at {trigger_time.strftime('%H:%M:%S')}. Current IST: {now.strftime('%H:%M:%S')}")

                    if now >= trigger_time:
                        print(f"[DEBUG-TRIGGER] TRIGGERING order {order.id} (status: scheduled -> pending)")
                        order.status = "pending"
                        triggered_count += 1
                        
                        # Also trigger linked ServiceRequest if it exists and is scheduled
                        sreqs = db.query(ServiceRequest).filter(
                            ServiceRequest.food_order_id == order.id,
                            ServiceRequest.status == "scheduled",
                            ServiceRequest.branch_id == branch_id
                        ).all()

                        for sreq in sreqs:
                            print(f"[DEBUG-TRIGGER] TRIGGERING linked service request {sreq.id} (status: scheduled -> pending)")
                            sreq.status = "pending"
                except ValueError as ve:
                    print(f"[DEBUG-TRIGGER] Error parsing time for order {order.id}: {ve}")
        
        if triggered_count > 0:
            db.commit()
            print(f"[DEBUG-TRIGGER] Successfully triggered {triggered_count} orders/tasks.")
            
    except Exception as e:
        print(f"Error checking scheduled orders: {e}")
        import traceback
        traceback.print_exc()

    return True
