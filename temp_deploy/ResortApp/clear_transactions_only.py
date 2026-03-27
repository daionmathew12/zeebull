"""
Clear Transactions Only - Preserves Master Data (Menu, Inventory, Rooms, etc.)
Clears:
- Bookings & Checkouts
- Billing & Payments
- Food Orders & KOTs
- Services & Requests
- Inventory Transactions (Stock history, Purchase Orders)
- Notifications & Suggestions

Preserves:
- Users (Admin, Staff)
- Rooms (Layout)
- Food Items (Menu)
- Services (Catalog)
- Packages (Catalog)
- Inventory Items (Catalog)
- Vendors
"""

from sqlalchemy import text
from app.database import SessionLocal
from datetime import datetime

def clear_transactions():
    """Clear all transactional data but keep master data"""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("CLEAR TRANSACTIONS ONLY")
        print("=" * 60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Delete in correct order to avoid foreign key constraints
        # Child tables first, then parents
        tables = [
            # Level 1: Logs & Notifications
            "notifications",
            "suggestions",
            "working_logs",
            "attendance",
            "waste_logs",
            
            # Level 2: Inventory & Stock Transaction details
            "stock_issue_details",
            "stock_requisition_details",
            "purchase_details",
            "inventory_transactions",
            "location_stocks",
            "employee_inventory_assignments",
            "asset_registry",
            "asset_mappings",
            
            # Level 3: Inventory Headers
            "stock_issues",
            "stock_requisitions",
            "purchase_masters",
            
            # Level 4: Checkout & Payment details
            "checkout_payments",
            "checkout_verifications",
            "checkout_requests",
            
            # Level 5: Checkouts (link bookings)
            "checkouts",
            
            # Level 6: Service & Food Orders
            "assigned_services",
            "service_requests",
            "food_order_items",
            "food_orders",
            
            # Level 7: Bookings
            "package_booking_rooms",
            "booking_rooms",
            "package_bookings",
            "bookings",
            
            # Level 8: Finance
            "expenses",
            "payments",
            "journal_entry_lines",
            "journal_entries",
        ]
        
        print("-" * 60)
        print("CLEARING TABLES")
        print("-" * 60)
        
        total_cleared = 0
        for table in tables:
            try:
                # Check if table exists first (to be safe)
                check_query = text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')")
                exists = db.execute(check_query).scalar()
                
                if exists:
                    result = db.execute(text(f"DELETE FROM {table}"))
                    if result.rowcount > 0:
                        print(f"✓ Cleared {result.rowcount:4d} from {table}")
                        total_cleared += result.rowcount
                    db.commit()
                else:
                    print(f"  - Table {table} not found (skipped)")
            except Exception as e:
                db.rollback()
                print(f"  ⚠ Error clearing {table}: {str(e)[:100]}")

        print("-" * 60)
        print("RESETTING VALUES")
        print("-" * 60)
        
        # Reset Room Status
        try:
            result = db.execute(text("UPDATE rooms SET status = 'Available'"))
            db.commit()
            print(f"✓ Reset {result.rowcount} rooms to 'Available'")
        except Exception as e:
            print(f"  ⚠ Error resetting rooms: {str(e)}")
            
        # Reset Inventory Stock Counts
        try:
            result = db.execute(text("UPDATE inventory_items SET current_stock = 0"))
            db.commit()
            print(f"✓ Reset stock count to 0 for {result.rowcount} inventory items")
        except Exception as e:
            print(f"  ⚠ Error resetting inventory stock: {str(e)}")

        print("\n" + "=" * 60)
        print("✅ TRANSACTION CLEANUP COMPLETED")
        print("=" * 60)
        print("🔄 Please refresh your browser app")
        print()
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("\n⚠️  WARNING: This will delete all TRANSACTION history!")
    print("This includes: Bookings, Orders, Payments, Inventory Logs etc.")
    print("But keeps: Menu, Rooms, Staff, Inventory Items catalog.\n")
    
    response = input("Continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        clear_transactions()
    else:
        print("Cancelled.")
