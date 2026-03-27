def create_waste_log(db: Session, data: dict, reported_by: int):
    from app.models.inventory import WasteLog, InventoryTransaction, InventoryItem
    from app.models.food import FoodItem
    from datetime import datetime
    
    is_food = data.get("is_food_item", False)
    
    if is_food:
        # Handle food item waste
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
        # Existing inventory item logic
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
