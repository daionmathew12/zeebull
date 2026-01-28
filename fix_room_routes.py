# Read the file
with open('/var/www/inventory/ResortApp/app/api/room.py', 'r') as f:
    content = f.read()

# Remove the duplicate endpoints at the end
if '# ---------------- ROOM ACTIVITY TRACKING' in content:
    parts = content.split('# ---------------- ROOM ACTIVITY TRACKING')
    content = parts[0].rstrip() + '\n'

# Find the position to insert (before @router.delete("/{room_id}"))
lines = content.split('\n')
insert_pos = None
for i, line in enumerate(lines):
    if '@router.delete("/{room_id}")' in line:
        # Check it's not the test endpoint
        if i > 0 and 'test' not in lines[i-5:i]:
            insert_pos = i
            break

if insert_pos:
    endpoint_code = '''
# ---------------- ROOM ACTIVITY TRACKING ----------------
@router.get("/{room_id}/inventory-usage")
def get_room_inventory_usage(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    from app.models.inventory import InventoryTransaction, InventoryItem
    from app.models.employee import Employee
    
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
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
            "guest_used": trans.transaction_type == 'sale',
            "transaction_type": trans.transaction_type,
            "notes": trans.notes
        })
    
    return result

@router.get("/{room_id}/activity-log")
def get_room_activity_log(
    room_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    from app.models.service_request import ServiceRequest
    from app.models.employee import Employee
    
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    activities = []
    
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
    
    bookings = db.query(Booking).join(BookingRoom).filter(
        BookingRoom.room_id == room_id
    ).order_by(Booking.check_in.desc()).limit(20).all()
    
    for booking in bookings:
        activities.append({
            "type": "booking",
            "description": f"Guest check-in: {booking.guest_name}",
            "performed_by": "Front Desk",
            "timestamp": booking.check_in.isoformat() if booking.check_in else None,
            "status": booking.status
        })
        
        if booking.check_out and booking.status in ['checked-out', 'completed']:
            activities.append({
                "type": "booking",
                "description": f"Guest check-out: {booking.guest_name}",
                "performed_by": "Front Desk",
                "timestamp": booking.check_out.isoformat(),
                "status": booking.status
            })
    
    activities.sort(key=lambda x: x['timestamp'] if x['timestamp'] else '', reverse=True)
    
    return activities[:100]

'''
    lines.insert(insert_pos, endpoint_code)
    content = '\n'.join(lines)
    
    with open('/var/www/inventory/ResortApp/app/api/room.py', 'w') as f:
        f.write(content)
    
    print('SUCCESS: Routes inserted at correct position')
else:
    print('ERROR: Could not find insertion point')
