# ---------------- ROOM ACTIVITY TRACKING ----------------
@router.get("/{room_id}/inventory-usage")
def get_room_inventory_usage(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get inventory usage history for a specific room.
    Returns items consumed/used in this room with employee and guest information.
    """
    try:
        from app.models.inventory import InventoryTransaction, InventoryItem
        from app.models.employee import Employee
        
        # Get room to verify it exists
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        
        # Get inventory transactions for this room's location
        if not room.inventory_location_id:
            return []
        
        transactions = db.query(InventoryTransaction).filter(
            InventoryTransaction.location_id == room.inventory_location_id
        ).order_by(InventoryTransaction.transaction_date.desc()).limit(100).all()
        
        result = []
        for trans in transactions:
            item = db.query(InventoryItem).filter(InventoryItem.id == trans.item_id).first()
            employee = db.query(Employee).filter(Employee.id == trans.employee_id).first() if trans.employee_id else None
            
            result.append({
                "item_name": item.name if item else "Unknown Item",
                "quantity": abs(trans.quantity) if trans.transaction_type in ['consumption', 'sale'] else trans.quantity,
                "used_by_name": employee.name if employee else "System",
                "used_at": trans.transaction_date.isoformat() if trans.transaction_date else None,
                "guest_used": trans.transaction_type == 'sale',  # Sales are typically guest-related
                "transaction_type": trans.transaction_type,
                "notes": trans.notes
            })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching room inventory usage: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching inventory usage: {str(e)}")

@router.get("/{room_id}/activity-log")
def get_room_activity_log(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get complete activity log for a specific room including:
    - Service requests
    - Cleaning/housekeeping
    - Bookings (check-ins/check-outs)
    - Maintenance activities
    """
    try:
        from app.models.service_request import ServiceRequest
        from app.models.employee import Employee
        
        # Get room to verify it exists
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        
        activities = []
        
        # 1. Service Requests
        service_requests = db.query(ServiceRequest).filter(
            ServiceRequest.room_id == room_id
        ).order_by(ServiceRequest.created_at.desc()).limit(50).all()
        
        for sr in service_requests:
            employee = db.query(Employee).filter(Employee.id == sr.employee_id).first() if sr.employee_id else None
            activities.append({
                "type": "service",
                "description": f"{sr.request_type}: {sr.description or 'No description'}",
                "performed_by": employee.name if employee else "Unassigned",
                "timestamp": sr.completed_at.isoformat() if sr.completed_at else sr.created_at.isoformat(),
                "status": sr.status
            })
        
        # 2. Bookings (Check-ins/Check-outs)
        bookings = db.query(Booking).join(BookingRoom).filter(
            BookingRoom.room_id == room_id
        ).order_by(Booking.check_in.desc()).limit(20).all()
        
        for booking in bookings:
            # Check-in activity
            activities.append({
                "type": "booking",
                "description": f"Guest check-in: {booking.guest_name}",
                "performed_by": "Front Desk",
                "timestamp": booking.check_in.isoformat() if booking.check_in else None,
                "status": booking.status
            })
            
            # Check-out activity (if applicable)
            if booking.check_out and booking.status in ['checked-out', 'completed']:
                activities.append({
                    "type": "booking",
                    "description": f"Guest check-out: {booking.guest_name}",
                    "performed_by": "Front Desk",
                    "timestamp": booking.check_out.isoformat(),
                    "status": booking.status
                })
        
        # Sort all activities by timestamp (most recent first)
        activities.sort(key=lambda x: x['timestamp'] if x['timestamp'] else '', reverse=True)
        
        return activities[:100]  # Return top 100 most recent activities
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching room activity log: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching activity log: {str(e)}")
