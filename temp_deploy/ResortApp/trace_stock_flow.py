"""
COMPREHENSIVE STOCK TRACE
Checks Purchases vs Transactions vs Current Stock for Beverages
"""
from app.database import SessionLocal
from app.models.inventory import InventoryItem, PurchaseDetail, PurchaseMaster, InventoryTransaction
from sqlalchemy import func

def trace_stock_flow():
    db = SessionLocal()
    try:
        print("="*80)
        print("STOCK FLOW ANALYSIS (Purchased vs Used vs Current)")
        print("="*80)
        
        items_to_check = ["Coca Cola 750ml", "Mineral Water 1L"]
        
        for name in items_to_check:
            # 1. Find Item
            item = db.query(InventoryItem).filter(InventoryItem.name.ilike(f"%{name}%")).first()
            
            if not item:
                print(f"\n❌ Item '{name}' NOT FOUND")
                continue
                
            print(f"\n📦 ANALYSIS FOR: {item.name} (ID: {item.id})")
            print("-" * 50)
            
            # 2. Check Purchases
            purchase_details = db.query(PurchaseDetail).filter(PurchaseDetail.item_id == item.id).all()
            total_purchased = sum([p.quantity for p in purchase_details])
            
            print(f"1. PURCHASE HISTORY:")
            if purchase_details:
                for p in purchase_details:
                    # Get date from master
                    master = db.query(PurchaseMaster).filter(PurchaseMaster.id == p.purchase_master_id).first()
                    date = master.purchase_date if master else "Unknown"
                    print(f"   + {p.quantity} (Date: {date})")
                print(f"   👉 TOTAL PURCHASED: {total_purchased}")
            else:
                print(f"   ⚠️ No purchase records found (0)")
            
            # 3. Check Transactions (All In/Out movements)
            txns = db.query(InventoryTransaction).filter(InventoryTransaction.item_id == item.id).order_by(InventoryTransaction.created_at).all()
            
            print(f"\n2. TRANSACTION HISTORY (Flow):")
            calculated_stock = 0
            
            if txns:
                for t in txns:
                    action = t.transaction_type
                    qty = t.quantity
                    
                    if action in ['in', 'purchase', 'return']:
                        calculated_stock += qty
                        sign = "+"
                    elif action in ['out', 'sale', 'waste', 'issue']:
                        calculated_stock -= qty
                        sign = "-"
                    elif action == 'transfer_in':
                        # Transfers within system don't change global stock usually, but let's see
                        sign = "(Transfer In)"
                    elif action == 'transfer_out':
                        sign = "(Transfer Out)"
                    else:
                        sign = "?"
                        
                    print(f"   {sign} {qty} ({action}) - Date: {t.created_at}")
                
                print(f"   👉 NET FLOW FROM TRANSACTIONS: {calculated_stock}")
            else:
                print(f"   ⚠️ No transaction records found")

            # 4. Compare with Current Stock
            print(f"\n3. CURRENT STATUS:")
            print(f"   👉 SYSTEM CURRENT STOCK: {item.current_stock}")
            
            # 5. Conclusion
            print(f"\n4. CONCLUSION:")
            if item.current_stock == 0 and total_purchased == 0:
                print("   ✅ Stock is 0 because NO PURCHASES have been made yet.")
                print("      (Or previous purchases were deleted during cleanup)")
            elif item.current_stock != total_purchased:
                print(f"   ⚠️ Mismatch found!")
                print("      Likely cause: Data cleanup reset stock to 0 but didn't delete all transactions,")
                print("      OR purchases were deleted but stock wasn't recalculated properly.")
            else:
                print("   ✅ Stock matches purchase history.")
                
            print("="*80)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    trace_stock_flow()
