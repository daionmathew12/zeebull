"""
Auto-apply all backend fixes for inventory system
Run this script to automatically update all backend files
"""

import re

# Fix 1: Update create_waste_log in app/curd/inventory.py
def fix_waste_crud():
    file_path = "app/curd/inventory.py"
    
    new_function = '''def create_waste_log(db: Session, data: dict, reported_by: int):
    from app.models.inventory import WasteLog, InventoryTransaction, InventoryItem
    from app.models.food import FoodItem
    from datetime import datetime
    
    is_food = data.get("is_food_item", False)
    
    if is_food:
        food_item_id = data.get("food_item_id")
        if not food_item_id:
            raise ValueError("Food item ID is required for food waste")
        
        food_item = db.query(FoodItem).filter(FoodItem.id == food_item_id).first()
        if not food_item:
            raise ValueError("Food item not found")
        
        log_number = generate_waste_log_number(db)
        waste_log = WasteLog(
            log_number=log_number,
            food_item_id=food_item_id,
            is_food_item=True,
            location_id=data.get("location_id"),
            quantity=data["quantity"],
            unit=data["unit"],
            reason_code=data["reason_code"],
            action_taken=data.get("action_taken"),
            photo_path=data.get("photo_path"),
            notes=data.get("notes"),
            reported_by=reported_by,
            waste_date=data.get("waste_date", datetime.utcnow()),
        )
        db.add(waste_log)
        
    else:
        item_id = data.get("item_id")
        if not item_id:
            raise ValueError("Item ID is required for inventory waste")
        
        item = get_item_by_id(db, item_id)
        if not item:
            raise ValueError("Item not found")
        
        if item.current_stock < data["quantity"]:
            raise ValueError(f"Insufficient stock for {item.name}. Available: {item.current_stock}, Reported: {data['quantity']}")
        
        log_number = generate_waste_log_number(db)
        waste_log = WasteLog(
            log_number=log_number,
            item_id=item_id,
            is_food_item=False,
            location_id=data.get("location_id"),
            batch_number=data.get("batch_number"),
            expiry_date=data.get("expiry_date"),
            quantity=data["quantity"],
            unit=data["unit"],
            reason_code=data["reason_code"],
            action_taken=data.get("action_taken"),
            photo_path=data.get("photo_path"),
            notes=data.get("notes"),
            reported_by=reported_by,
            waste_date=data.get("waste_date", datetime.utcnow()),
        )
        db.add(waste_log)
        
        item.current_stock -= data["quantity"]
        
        transaction = InventoryTransaction(
            item_id=item_id,
            transaction_type="out",
            quantity=data["quantity"],
            unit_price=item.unit_price,
            total_amount=item.unit_price * data["quantity"] if item.unit_price else None,
            reference_number=log_number,
            notes=f"Waste/Spoilage: {data['reason_code']} - {data.get('notes', '')}",
            created_by=reported_by
        )
        db.add(transaction)
    
    db.commit()
    db.refresh(waste_log)
    return waste_log
'''
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and replace the create_waste_log function
    pattern = r'def create_waste_log\(db: Session, data: dict, reported_by: int\):.*?(?=\n\ndef |\nclass |\Z)'
    content = re.sub(pattern, new_function, content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed create_waste_log in app/curd/inventory.py")

# Fix 2: Update waste API endpoint
def fix_waste_api():
    file_path = "app/api/inventory.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the waste log endpoint and update parameters
    old_params = '''def create_waste_log(
    item_id: int = Form(...),
    location_id: Optional[int] = Form(None),'''
    
    new_params = '''def create_waste_log(
    item_id: Optional[int] = Form(None),
    food_item_id: Optional[int] = Form(None),
    is_food_item: bool = Form(False),
    location_id: Optional[int] = Form(None),'''
    
    content = content.replace(old_params, new_params)
    
    # Update waste_data dict
    old_data = '''waste_data = {
            "item_id": item_id,
            "location_id": int(location_id) if location_id else None,'''
    
    new_data = '''waste_data = {
            "item_id": item_id,
            "food_item_id": food_item_id,
            "is_food_item": is_food_item,
            "location_id": int(location_id) if location_id else None,'''
    
    content = content.replace(old_data, new_data)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed waste API endpoint in app/api/inventory.py")

# Fix 3: Update purchase status logic
def fix_purchase_update():
    print("⚠️  Purchase update function needs manual review")
    print("   See BACKEND_IMPLEMENTATION_CODE.md for complete code")

if __name__ == "__main__":
    print("🚀 Starting backend fixes...")
    print()
    
    try:
        fix_waste_crud()
        fix_waste_api()
        fix_purchase_update()
        print()
        print("✅ Backend fixes applied!")
        print("   Backend server should auto-reload")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("   Please apply fixes manually using BACKEND_IMPLEMENTATION_CODE.md")
