from app.database import SessionLocal
from app.models.inventory import Location, LocationStock, StockIssue, StockIssueDetail, InventoryItem
from sqlalchemy import func

db = SessionLocal()

def check_room(room_num):
    print(f"\nSearching for Room {room_num}...")
    loc = db.query(Location).filter(Location.name.ilike(f"%{room_num}%")).first()
    if not loc:
        print("Not found by name. Checking room_area...")
        loc = db.query(Location).filter(Location.room_area.ilike(f"%{room_num}%")).first()
    
    if not loc:
        print("Location Not Found.")
        return

    print(f"Found Location: ID={loc.id} Name='{loc.name}' Type='{loc.location_type}'")

    # 1. Check LocationStock (Current Total)
    stocks = db.query(LocationStock).filter(LocationStock.location_id == loc.id).all()
    print("\n--- Current Location Stock (Total Qty) ---")
    if not stocks:
        print("No stock records.")
    for s in stocks:
        item = db.query(InventoryItem).get(s.item_id)
        print(f"Item: {item.name} (ID: {item.id}) | Qty: {s.quantity}")

    # 2. Check Stock Issues (History)
    print("\n--- Stock Issue History (Inbound) ---")
    issues = db.query(StockIssue).filter(StockIssue.destination_location_id == loc.id).all()
    if not issues:
        print("No stock issues found.")
    
    for i in issues:
        print(f"Issue #{i.id} (Ref: {i.issue_number}) Date: {i.issue_date}")
        for d in i.details:
            item = db.query(InventoryItem).get(d.item_id)
            print(f"  > Item: {item.name} | Qty: {d.issued_quantity} | Payable: {d.is_payable} | UnitPrice: {d.unit_price} | Rental: {d.rental_price}")

    # 3. Check Logic Simulation
    print("\n--- Breakdown Logic Check ---")
    # Simulate the logic from get_location_items
    for s in stocks:
        item_id = s.item_id
        qty = float(s.quantity)
        
        # Get matching issues
        details_query = db.query(StockIssueDetail).join(StockIssue).filter(
            StockIssue.destination_location_id == loc.id,
            StockIssueDetail.item_id == item_id
        ).order_by(StockIssue.issue_date.desc()).all()
        
        good_issues = [d for d in details_query if not d.is_damaged]
        
        complim = 0.0
        payable = 0.0
        rem = qty
        
        for d in good_issues:
            if rem <= 0: break
            issued = float(d.issued_quantity)
            attributed = min(rem, issued)
            
            if d.is_payable:
                payable += attributed
            else:
                complim += attributed
            
            rem -= attributed
            
        print(f"Item {item_id}: Total={qty} -> Calculated: Comp={complim}, Pay={payable}. Remaining (Unattributed)={rem}")

if __name__ == "__main__":
    check_room("101")
