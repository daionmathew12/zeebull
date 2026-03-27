
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import random

# Add parent directory to path
sys.path.append(os.getcwd())

from app.database import SQLALCHEMY_DATABASE_URL
from app.models.inventory import (
    Location, LocationStock, InventoryItem, InventoryTransaction, 
    PurchaseMaster, PurchaseDetail, Vendor
)
from app.models.user import User

def create_comprehensive_stock_purchase():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        print("--- CREATING COMPREHENSIVE PURCHASE (ALL ITEMS) ---")
        
        # 1. SETUP CONTEXT
        # User
        admin = db.query(User).filter(User.email == "admin@example.com").first()
        if not admin: admin = db.query(User).first()
        user_id = admin.id if admin else 1
        
        # Warehouse
        warehouse = db.query(Location).filter(Location.location_type.in_(['WAREHOUSE', 'CENTRAL_WAREHOUSE'])).first()
        if not warehouse: warehouse = db.query(Location).first()
        print(f"Destination Location: {warehouse.name} (ID: {warehouse.id})")
        
        # Vendor
        vendor = db.query(Vendor).first()
        if not vendor:
            print("No vendor found! Creating a default vendor.")
            vendor = Vendor(name="Default Supplier", contact_person="Sales", phone="0000000000")
            db.add(vendor)
            db.flush()
        print(f"Vendor: {vendor.name} (ID: {vendor.id})")

        # 2. CREATE PURCHASE HEADER
        po_number = f"PO-AUTO-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
        
        purchase = PurchaseMaster(
            purchase_number=po_number,
            vendor_id=vendor.id,
            purchase_date=datetime.utcnow(),
            status="received", # Auto-receive
            destination_location_id=warehouse.id,
            created_by=user_id,
            sub_total=0,
            total_amount=0,
            payment_status="paid",
            notes="Auto-generated comprehensive stock replenishment"
        )
        db.add(purchase)
        db.flush()
        print(f"Created Purchase Master: {po_number}")

        # 3. ADD ITEMS
        all_items = db.query(InventoryItem).filter(InventoryItem.is_active == True).all()
        print(f"Found {len(all_items)} active inventory items.")
        
        grand_total = 0.0
        
        for item in all_items:
            qty_to_add = 20 # Minimum 10 asked, giving 20 buffer
            
            # Special cases for consumables that need more
            name_lower = item.name.lower()
            if "water" in name_lower or "cola" in name_lower or "soap" in name_lower:
                qty_to_add = 100
            if item.unit and item.unit.lower() == "kg":
                qty_to_add = 50
            if "copier" in name_lower or "paper" in name_lower:
                qty_to_add = 50
                
            unit_price = item.unit_price or 100.0
            if unit_price <= 0: unit_price = 100.0
            
            line_total = qty_to_add * unit_price
            grand_total += line_total
            
            # Create Detail
            detail = PurchaseDetail(
                purchase_master_id=purchase.id,
                item_id=item.id,
                quantity=qty_to_add,
                unit=item.unit or "pcs",
                unit_price=unit_price,
                total_amount=line_total,
                gst_rate=item.gst_rate or 0,
                sgst_amount=0,
                cgst_amount=0,
                igst_amount=0
            )
            db.add(detail)
            
            # 4. UPDATE STOCK (Because status is 'received')
            
            # Global Stock
            old_global = item.current_stock or 0
            item.current_stock = old_global + qty_to_add
            
            # Location Stock
            loc_stock = db.query(LocationStock).filter(
                LocationStock.location_id == warehouse.id,
                LocationStock.item_id == item.id
            ).first()
            
            if loc_stock:
                loc_stock.quantity += qty_to_add
                loc_stock.last_updated = datetime.utcnow()
            else:
                new_ls = LocationStock(
                    location_id=warehouse.id,
                    item_id=item.id,
                    quantity=qty_to_add,
                    last_updated=datetime.utcnow()
                )
                db.add(new_ls)
                
            # Transaction Log
            txn = InventoryTransaction(
                item_id=item.id,
                transaction_type="in",
                quantity=qty_to_add,
                unit_price=unit_price,
                total_amount=line_total,
                reference_number=po_number,
                purchase_master_id=purchase.id,
                notes="Auto-replenishment",
                created_by=user_id,
                created_at=datetime.utcnow()
            )
            db.add(txn)
            
        # Update Purchase Totals
        purchase.sub_total = grand_total
        purchase.total_amount = grand_total
        
        db.commit()
        print(f"✅ SUCCESSFULLY CREATED PURCHASE {po_number}")
        print(f"   Items processed: {len(all_items)}")
        print(f"   Total Value: {grand_total}")
        print("   All stock levels updated.")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    create_comprehensive_stock_purchase()
