"""Fix purchase stock management"""
import re

file_path = "app/api/inventory.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the update_purchase function
start_marker = '@router.put("/purchases/{purchase_id}", response_model=PurchaseMasterOut)'
end_marker = '\n\n@router.delete("/purchases'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker, start_idx)

if start_idx == -1 or end_idx == -1:
    print("❌ Could not find function boundaries")
    exit(1)

new_function = '''@router.put("/purchases/{purchase_id}", response_model=PurchaseMasterOut)
def update_purchase(
    purchase_id: int,
    purchase_update: PurchaseMasterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.inventory import InventoryItem, InventoryTransaction, LocationStock
    
    purchase = inventory_crud.get_purchase_by_id(db, purchase_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    old_status = purchase.status
    new_status = purchase_update.status if hasattr(purchase_update, 'status') else old_status
    
    updated = inventory_crud.update_purchase_master(db, purchase_id, purchase_update)
    if not updated:
        raise HTTPException(status_code=400, detail="Cannot update purchase")
    
    # CASE 1: Purchase RECEIVED
    if new_status == "received" and old_status != "received":
        for detail in updated.details:
            if not detail.item_id:
                continue
            
            item = db.query(InventoryItem).filter(InventoryItem.id == detail.item_id).first()
            if not item:
                continue
            
            # Weighted average cost
            old_stock = item.current_stock or 0
            old_price = item.unit_price or 0
            old_value = old_stock * old_price
            
            new_stock = detail.quantity
            new_price = detail.unit_price
            new_value = new_stock * new_price
            
            total_stock = old_stock + new_stock
            total_value = old_value + new_value
            
            item.current_stock = total_stock
            if total_stock > 0:
                item.unit_price = round(total_value / total_stock, 2)
            
            print(f"[RECEIVED] {item.name}: Stock {old_stock}→{total_stock}, Cost ₹{old_price}→₹{item.unit_price}")
            
            # Location stock
            if updated.destination_location_id:
                location_stock = db.query(LocationStock).filter(
                    LocationStock.location_id == updated.destination_location_id,
                    LocationStock.item_id == detail.item_id
                ).first()
                
                if location_stock:
                    location_stock.quantity += detail.quantity
                else:
                    location_stock = LocationStock(
                        location_id=updated.destination_location_id,
                        item_id=detail.item_id,
                        quantity=detail.quantity
                    )
                    db.add(location_stock)
            
            # Transaction
            transaction = InventoryTransaction(
                item_id=detail.item_id,
                transaction_type="in",
                quantity=detail.quantity,
                unit_price=detail.unit_price,
                total_amount=detail.unit_price * detail.quantity,
                reference_number=updated.purchase_number,
                notes=f"Purchase received: {updated.purchase_number}",
                created_by=current_user.id
            )
            db.add(transaction)
    
    # CASE 2: Purchase CANCELLED
    elif new_status == "cancelled" and old_status == "received":
        for detail in updated.details:
            if not detail.item_id:
                continue
            
            item = db.query(InventoryItem).filter(InventoryItem.id == detail.item_id).first()
            if not item:
                continue
            
            old_stock = item.current_stock
            new_stock = max(0, old_stock - detail.quantity)
            
            old_value = old_stock * item.unit_price
            cancelled_value = detail.quantity * detail.unit_price
            remaining_value = old_value - cancelled_value
            
            item.current_stock = new_stock
            if new_stock > 0:
                item.unit_price = round(remaining_value / new_stock, 2)
            
            print(f"[CANCELLED] {item.name}: Stock {old_stock}→{new_stock}")
            
            if updated.destination_location_id:
                location_stock = db.query(LocationStock).filter(
                    LocationStock.location_id == updated.destination_location_id,
                    LocationStock.item_id == detail.item_id
                ).first()
                
                if location_stock:
                    location_stock.quantity -= detail.quantity
                    if location_stock.quantity <= 0:
                        db.delete(location_stock)
            
            transaction = InventoryTransaction(
                item_id=detail.item_id,
                transaction_type="out",
                quantity=detail.quantity,
                unit_price=detail.unit_price,
                total_amount=detail.unit_price * detail.quantity,
                reference_number=updated.purchase_number,
                notes=f"Purchase cancelled: {updated.purchase_number}",
                created_by=current_user.id
            )
            db.add(transaction)
    
    db.commit()
    return get_purchase(purchase_id, db, current_user)
'''

# Replace
new_content = content[:start_idx] + new_function + content[end_idx:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Purchase stock management fixed!")
