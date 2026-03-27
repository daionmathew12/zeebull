from app.database import SessionLocal
from app.models.inventory import PurchaseMaster
from app.models.account import JournalEntry
from app.utils.accounting_helpers import create_purchase_journal_entry
from app.models.inventory import Vendor
from app.api.gst_reports import RESORT_STATE_CODE

db = SessionLocal()
try:
    purchases = db.query(PurchaseMaster).all()
    for p in purchases:
        # Check logic: create if confirmed OR received
        if p.status in ["confirmed", "received"]:
            existing_entry = db.query(JournalEntry).filter(
                JournalEntry.reference_type == 'purchase',
                JournalEntry.reference_id == p.id
            ).first()
            
            if not existing_entry:
                print(f"Creating missing JE for Purchase #{p.id} ({p.status})")
                
                # Fetch vendor details
                vendor = db.query(Vendor).filter(Vendor.id == p.vendor_id).first()
                vendor_name = (vendor.legal_name or vendor.name) if vendor else "Unknown"
                
                # Determine if inter-state
                is_interstate = False
                if vendor and vendor.gst_number and len(vendor.gst_number) >= 2:
                    vendor_state_code = vendor.gst_number[:2]
                    is_interstate = vendor_state_code != RESORT_STATE_CODE
                
                create_purchase_journal_entry(
                    db=db,
                    purchase_id=p.id,
                    vendor_id=p.vendor_id,
                    inventory_amount=float(p.sub_total or 0),
                    cgst_amount=float(p.cgst or 0),
                    sgst_amount=float(p.sgst or 0),
                    igst_amount=float(p.igst or 0),
                    vendor_name=vendor_name,
                    is_interstate=is_interstate,
                    created_by=1  # Admin
                )
    db.commit()
    print("Fix complete.")
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
