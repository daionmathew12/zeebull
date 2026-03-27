import re

# Read the file
with open(r'c:\releasing\orchid\ResortApp\app\api\checkout.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Change complimentary limit to 0 (line ~1465)
content = content.replace(
    'limit = inv_item.complimentary_limit or 0',
    'limit = 0  # Charge for all items by default'
)

# Fix 2: Add cleanup code after "room.status = \"Available\""
cleanup_code = '''
            
            # 13.1. Return remaining consumables to warehouse
            try:
                if room.inventory_location_id:
                    from app.models.inventory import LocationStock, Location, InventoryTransaction, InventoryItem
                    from sqlalchemy.orm import joinedload
                    
                    remaining = db.query(LocationStock).join(InventoryItem).options(
                        joinedload(LocationStock.item)
                    ).filter(
                        LocationStock.location_id == room.inventory_location_id,
                        LocationStock.quantity > 0,
                        InventoryItem.is_fixed_asset == False
                    ).all()
                    
                    if remaining:
                        warehouse = db.query(Location).filter(Location.location_type == "WAREHOUSE").first()
                        if warehouse:
                            for item_stock in remaining:
                                qty = item_stock.quantity
                                item_name = item_stock.item.name if item_stock.item else f"Item #{item_stock.item_id}"
                                
                                wh_stock = db.query(LocationStock).filter(
                                    LocationStock.location_id == warehouse.id,
                                    LocationStock.item_id == item_stock.item_id
                                ).first()
                                
                                if wh_stock:
                                    wh_stock.quantity += qty
                                    wh_stock.last_updated = datetime.utcnow()
                                else:
                                    db.add(LocationStock(
                                        location_id=warehouse.id,
                                        item_id=item_stock.item_id,
                                        quantity=qty,
                                        last_updated=datetime.utcnow()
                                    ))
                                
                                db.add(InventoryTransaction(
                                    item_id=item_stock.item_id,
                                    transaction_type="transfer_out",
                                    quantity=-qty,
                                    location_id=room.inventory_location_id,
                                    destination_location_id=warehouse.id,
                                    transaction_date=datetime.utcnow(),
                                    notes=f"Checkout cleanup - returned from Room {room.number}",
                                    user_id=current_user.id if current_user else None
                                ))
                                
                                item_stock.quantity = 0
                                item_stock.last_updated = datetime.utcnow()
                                print(f"[CLEANUP] Returned {qty} x {item_name} from Room {room.number}")
            except Exception as e:
                print(f"[WARNING] Cleanup failed: {e}")
'''

# Find and replace the room status line
pattern = r'(            room\.status = "Available"[^\r\n]*\r?\n)'
replacement = r'\1' + cleanup_code
content = re.sub(pattern, replacement, content)

# Write back
with open(r'c:\releasing\orchid\ResortApp\app\api\checkout.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Applied both fixes successfully!")
