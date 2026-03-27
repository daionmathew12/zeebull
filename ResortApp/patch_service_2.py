
import sys
from datetime import datetime

new_logic = """                            # --- CLEANED UP RETURN/USAGE/LAUNDRY/WASTE PROCESSING ---
                            quantity_returned = float(return_item.quantity_returned or 0.0)
                            quantity_used = float(getattr(return_item, 'quantity_used', 0.0) or 0.0)
                            quantity_damaged = float(getattr(return_item, 'quantity_damaged', 0.0) or 0.0)
                            
                            item = assignment.item
                            
                            # Auto-infer usage if everything else is 0 and it's successful completion
                            if quantity_used == 0 and quantity_returned == 0 and quantity_damaged == 0 and new_status == "completed":
                                quantity_used = assignment.balance_quantity
                            
                            # 1. Update assignment record
                            assignment.quantity_used += quantity_used
                            assignment.quantity_returned += quantity_returned
                            
                            # Calculate missing quantity
                            balance = assignment.quantity_assigned - assignment.quantity_used - assignment.quantity_returned
                            quantity_missing = max(0, balance - quantity_damaged)
                            
                            print(f"[DEBUG] Return processing: Item={item.name}, Assigned={assignment.quantity_assigned}, Used={assignment.quantity_used}, Returned={assignment.quantity_returned}, Damaged={quantity_damaged}, Missing={quantity_missing}")

                            # 2. Handle Used items (Textile vs Consumable)
                            if quantity_used > 0:
                                is_textile = False
                                try:
                                    is_textile = item.track_laundry_cycle or (item.category and item.category.track_laundry)
                                except: pass
                                    
                                if is_textile:
                                    # MOVEMENT TO LAUNDRY
                                    laundry_loc = db.query(Location).filter(
                                        ((Location.name.ilike("%Laundry%")) | (Location.location_type == "LAUNDRY")),
                                        Location.branch_id == assigned.branch_id
                                    ).first()
                                    
                                    if not laundry_loc:
                                        print(f"[INFO] Creating missing Laundry location for Branch {assigned.branch_id}")
                                        laundry_loc = Location(
                                            name="Laundry", 
                                            location_type="LAUNDRY", 
                                            building="Main", 
                                            room_area="Laundry Area",
                                            branch_id=assigned.branch_id, 
                                            is_inventory_point=True
                                        )
                                        db.add(laundry_loc); db.flush()
                                    
                                    # Record Laundry Transaction
                                    db.add(InventoryTransaction(
                                        item_id=item.id, transaction_type="laundry", quantity=quantity_used,
                                        unit_price=item.unit_price, total_amount=0,
                                        reference_number=f"LNDRY-COL-{assigned_id}", department="Laundry",
                                        destination_location_id=laundry_loc.id,
                                        source_location_id=assigned.room.inventory_location_id if assigned.room else None,
                                        notes=f"Auto-collected Dirty Linen from Room {assigned.room.number if assigned.room else 'Unknown'} (Svc: {assigned.service.name})",
                                        created_by=updated_by, branch_id=assigned.branch_id, created_at=datetime.utcnow()
                                    ))
                                    
                                    # Add to LaundryLog
                                    from app.models.inventory import LaundryLog
                                    db.add(LaundryLog(
                                        item_id=item.id, quantity=quantity_used, status="Incomplete Washing",
                                        source_location_id=assigned.room.inventory_location_id if assigned.room else None,
                                        room_number=assigned.room.number if assigned.room else 'Unknown',
                                        notes=f"Auto-collected during service {assigned.service.name}", branch_id=assigned.branch_id
                                    ))
                                    
                                    # Update Stock in Laundry Location
                                    from app.models.inventory import LocationStock
                                    l_stock = db.query(LocationStock).filter(LocationStock.location_id == laundry_loc.id, LocationStock.item_id == item.id).first()
                                    if l_stock: l_stock.quantity += quantity_used
                                    else: db.add(LocationStock(location_id=laundry_loc.id, item_id=item.id, quantity=quantity_used, branch_id=assigned.branch_id))
                                    
                                    item.current_stock += quantity_used
                                else:
                                    # REGULAR USAGE
                                    db.add(InventoryTransaction(
                                        item_id=item.id, transaction_type="out", quantity=quantity_used,
                                        unit_price=item.unit_price, total_amount=quantity_used * (item.unit_price or 0.0),
                                        reference_number=f"SVC-USAGE-{assigned_id}",
                                        department=item.category.name if item.category else "Housekeeping",
                                        notes=f"Consumed during Service: {assigned.service.name}",
                                        created_by=updated_by, branch_id=assigned.branch_id, created_at=datetime.utcnow()
                                    ))

                            # 3. Handle Clean Returns (Back to Store)
                            if quantity_returned > 0:
                                item.current_stock += round(quantity_returned, 4)
                                dest_loc = global_return_location
                                if hasattr(return_item, 'return_location_id') and return_item.return_location_id:
                                    spec_loc = db.query(Location).filter(Location.id == return_item.return_location_id).first()
                                    if spec_loc: dest_loc = spec_loc
                                
                                if dest_loc:
                                    from app.models.inventory import LocationStock
                                    lstk = db.query(LocationStock).filter(LocationStock.location_id == dest_loc.id, LocationStock.item_id == item.id).first()
                                    if lstk: lstk.quantity += round(quantity_returned, 4)
                                    else: db.add(LocationStock(location_id=dest_loc.id, item_id=item.id, quantity=round(quantity_returned, 4), branch_id=assigned.branch_id))

                                db.add(InventoryTransaction(
                                    item_id=item.id, transaction_type="transfer_in", quantity=round(quantity_returned, 4),
                                    unit_price=item.unit_price, total_amount=0, reference_number=f"SVC-RETURN-{assigned_id}",
                                    department="Housekeeping", notes=f"Return to {dest_loc.name if dest_loc else 'Office'}",
                                    created_by=updated_by, branch_id=assigned.branch_id
                                ))

                            # 4. Handle Damaged/Missing (Waste Logs)
                            for w_qty, reason in [(quantity_damaged, "Damaged"), (quantity_missing, "Missing")]:
                                if w_qty > 0:
                                    waste_data = {"item_id": item.id, "quantity": w_qty, "unit": item.unit or "pcs", "reason_code": reason, "notes": f"Auto-reported during {assigned.service.name}", "location_id": (assigned.room.inventory_location_id if assigned.room else assigned.room_id)}
                                    reporter_id = assigned.employee.user_id if assigned.employee and assigned.employee.user_id else 1
                                    from app.curd import inventory as crud_inventory
                                    crud_inventory.create_waste_log(db, waste_data, reported_by=reporter_id, branch_id=assigned.branch_id)

                            # Finalize Status
                            if (assignment.quantity_returned + assignment.quantity_used + quantity_damaged + quantity_missing) >= assignment.quantity_assigned:
                                assignment.is_returned = True; assignment.status = "returned"; assignment.returned_at = datetime.utcnow()
                            else: assignment.status = "partially_returned" """

with open('app/curd/service.py', 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = '                            # --- CLEANED UP RETURN/USAGE/LAUNDRY/WASTE PROCESSING ---'
end_marker = '                                assignment.is_returned = True; assignment.status = "returned"; assignment.returned_at = datetime.utcnow()'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker, start_idx + 1) + len(end_marker) + 53 # a bit extra for the else

# Better: find the end of the loop
loop_end_marker = '                            else: assignment.status = "partially_returned"'
end_idx = content.find(loop_end_marker, start_idx + 1) + len(loop_end_marker)

if start_idx != -1 and end_idx != -1:
    new_content = content[:start_idx] + new_logic + content[end_idx:]
    with open('app/curd/service.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('SUCCESS')
else:
    print(f'FAILURE: start={start_idx}, end={end_idx}')
