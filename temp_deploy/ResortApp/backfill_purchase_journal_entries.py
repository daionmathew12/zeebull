"""
Backfill Journal Entries for Existing Purchases
Creates journal entries for all 'received' purchases that don't have one yet.
"""
from app.database import SessionLocal
from app.models.inventory import PurchaseMaster, Vendor
from app.models.account import JournalEntry
from app.utils.accounting_helpers import create_purchase_journal_entry
from app.api.gst_reports import RESORT_STATE_CODE

db = SessionLocal()

print("=" * 70)
print("🔄 BACKFILLING PURCHASE JOURNAL ENTRIES")
print("=" * 70)

# Get all received purchases
purchases = db.query(PurchaseMaster).filter(
    PurchaseMaster.status == "received"
).all()

print(f"Found {len(purchases)} received purchases.")

created_count = 0
skipped_count = 0
error_count = 0

for purchase in purchases:
    try:
        # Check if journal entry already exists for this purchase
        existing_je = db.query(JournalEntry).filter(
            JournalEntry.reference_type == "purchase",
            JournalEntry.reference_id == purchase.id
        ).first()
        
        if existing_je:
            print(f"  ⏭️  PO-{purchase.purchase_number}: Journal Entry already exists ({existing_je.entry_number})")
            skipped_count += 1
            continue
            
        print(f"  📝 Processing PO-{purchase.purchase_number}...")
        
        # Get vendor details
        vendor = db.query(Vendor).filter(Vendor.id == purchase.vendor_id).first()
        vendor_name = (vendor.legal_name or vendor.name) if vendor else "Unknown"
        
        # Determine if inter-state purchase
        is_interstate = False
        if vendor and vendor.gst_number and len(vendor.gst_number) >= 2:
            vendor_state_code = vendor.gst_number[:2]
            is_interstate = vendor_state_code != RESORT_STATE_CODE
        
        # Calculate inventory amount (sub_total) and tax amounts
        inventory_amount = float(purchase.sub_total or 0)
        cgst_amount = float(purchase.cgst or 0)
        sgst_amount = float(purchase.sgst or 0)
        igst_amount = float(purchase.igst or 0)
        
        # Create journal entry
        je_id = create_purchase_journal_entry(
            db=db,
            purchase_id=purchase.id,
            vendor_id=purchase.vendor_id,
            inventory_amount=inventory_amount,
            cgst_amount=cgst_amount,
            sgst_amount=sgst_amount,
            igst_amount=igst_amount,
            vendor_name=vendor_name,
            is_interstate=is_interstate,
            created_by=purchase.created_by
        )
        
        created_count += 1
        print(f"     ✅ Created Journal Entry ID: {je_id}")
        
    except Exception as e:
        error_count += 1
        print(f"     ❌ Error: {str(e)}")

print("\n" + "=" * 70)
print("📊 SUMMARY")
print("=" * 70)
print(f"  Total Purchases: {len(purchases)}")
print(f"  Created: {created_count}")
print(f"  Skipped: {skipped_count}")
print(f"  Errors:  {error_count}")

db.close()
