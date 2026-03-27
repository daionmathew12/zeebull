from app.database import SessionLocal
from app.models.inventory import Location, InventoryItem, InventoryTransaction, LocationStock
from app.models.service import Service, AssignedService

def main():
    db = SessionLocal()
    try:
        # Check Laundry location
        laundry_loc = db.query(Location).filter(
            (Location.name.ilike("%Laundry%")) | 
            (Location.location_type == "LAUNDRY")
        ).first()
        
        print(f"Laundry Location Found: {laundry_loc.name if laundry_loc else 'None'} (ID: {laundry_loc.id if laundry_loc else 'None'})")

        # Find the service
        service = db.query(Service).filter(Service.name.ilike("%Couple%Relaxation%Massage%")).first()
        print(f"Service Found: {service.name if service else 'None'} (ID: {service.id if service else 'None'})")

        # Find bath towel item
        towel = db.query(InventoryItem).filter(InventoryItem.name.ilike("%Bath%Towel%")).first()
        print(f"Towel Found: {towel.name if towel else 'None'} (ID: {towel.id if towel else 'None'})")

        if service and towel:
            # Check recent transactions for this service and item
            txns = db.query(InventoryTransaction).filter(
                InventoryTransaction.item_id == towel.id,
                InventoryTransaction.notes.ilike(f"%{service.name}%")
            ).order_by(InventoryTransaction.created_at.desc()).limit(5).all()
            
            print(f"Recent Transactions for {towel.name} related to {service.name}:")
            for txn in txns:
                print(f" - {txn.created_at}: {txn.transaction_type} qty={txn.quantity}, notes='{txn.notes}', src={txn.source_location_id}, dest={txn.destination_location_id}")

            if laundry_loc:
                stock = db.query(LocationStock).filter(
                    LocationStock.location_id == laundry_loc.id,
                    LocationStock.item_id == towel.id
                ).first()
                print(f"Current Stock of {towel.name} in {laundry_loc.name}: {stock.quantity if stock else 'No record'}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
