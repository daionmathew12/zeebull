import sys, json
from app.database import SessionLocal
from app.models.employee import Employee
from app.curd.service_request import get_service_requests as crud_get
db = SessionLocal()
emp_id = 15
reqs = crud_get(db, limit=10, employee_id=emp_id)
print(f'crud_get returned {len(reqs)} items')
result = []
for sr in reqs:
    print(f"Processing sr.id={sr.id}")
    refill_data = None
    if sr.refill_data:
        try:
            refill_data = json.loads(sr.refill_data)
        except:
            refill_data = None
    
    try:
        food_order_data = None
        if sr.food_order:
            food_order_data = {
                "id": sr.food_order.id,
                "amount": sr.food_order.amount,
                "status": sr.food_order.status,
                "billing_status": sr.food_order.billing_status,
                "items": [
                    {
                        "id": item.id,
                        "food_item_id": item.food_item_id,
                        "food_item_name": item.food_item.name if item.food_item else "Unknown",
                        "quantity": item.quantity
                    } for item in sr.food_order.items
                ] if sr.food_order.items else []
            }

        result.append({
            "id": sr.id,
            "food_order_id": sr.food_order_id,
            "food_order": food_order_data,
            "room_id": sr.room_id,
            "employee_id": sr.employee_id,
            "request_type": str(sr.request_type) if sr.request_type else None,
            "type": str(sr.request_type) if sr.request_type else "Other", # Alias for mobile app
            "description": str(sr.description) if sr.description else None,
            "status": str(sr.status) if sr.status else "pending",
            "billing_status": sr.billing_status,
            "created_at": sr.created_at.isoformat() if sr.created_at else None,
            "completed_at": getattr(sr, 'completed_at').isoformat() if getattr(sr, 'completed_at', None) else None,
            "is_checkout_request": False,
            "is_assigned_service": False,
            "room_number": sr.room.number if sr.room else (str(getattr(sr, 'room_number', '')) if getattr(sr, 'room_number', None) else None),
            "employee_name": sr.employee.name if sr.employee else (str(getattr(sr, 'employee_name', '')) if getattr(sr, 'employee_name', None) else None),
            "refill_data": refill_data,
            "food_order_amount": sr.food_order.amount if sr.food_order else getattr(sr, 'food_order_amount', 0),
            "food_order_status": sr.food_order.status if sr.food_order else getattr(sr, 'food_order_status', None),
            "food_order_billing_status": sr.food_order.billing_status if sr.food_order else getattr(sr, 'food_order_billing_status', None),
            "food_items": food_order_data["items"] if food_order_data else []
        })
        print(f"Successfully processed sr.id={sr.id}")
    except Exception as e:
        print(f"[ERROR] Error converting service request {sr.id}: {e}")
        import traceback
        traceback.print_exc()
        continue
