"""
Clear All Inventory Master Data
This script removes all inventory items, categories, vendors, locations, and stock.
"""
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    print("=" * 80)
    print("CLEARING ALL INVENTORY MASTER DATA")
    print("=" * 80)
    print("\nThis will delete:")
    print("  - All inventory items")
    print("  - All inventory categories")
    print("  - All vendors")
    print("  - All inventory locations")
    print("  - All location stock")
    print("  - All asset mappings")
    print("  - All units of measurement")
    print("\nNOTE: Transactional data should already be cleared.")
    print("=" * 80)
    
    # Confirm
    response = input("\nAre you sure you want to proceed? (type 'YES' to confirm): ")
    if response != "YES":
        print("Operation cancelled.")
        db.close()
        exit()
    
    print("\nStarting cleanup...")
    
    # 1. Clear location stock
    print("\n[1/7] Clearing location stock...")
    db.execute(text("DELETE FROM location_stocks"))
    print("  ✓ Location stock cleared")
    
    # 2. Clear asset mappings
    print("[2/7] Clearing asset mappings...")
    db.execute(text("DELETE FROM asset_mappings"))
    print("  ✓ Asset mappings cleared")
    
    # 3. Clear recipe ingredients (references inventory items)
    print("[3/7] Clearing recipe ingredients...")
    db.execute(text("DELETE FROM recipe_ingredients"))
    print("  ✓ Recipe ingredients cleared")
    
    # 4. Clear inventory items
    print("[4/7] Clearing inventory items...")
    db.execute(text("DELETE FROM inventory_items"))
    print("  ✓ Inventory items cleared")
    
    # 5. Clear inventory categories
    print("[5/7] Clearing inventory categories...")
    db.execute(text("DELETE FROM inventory_categories"))
    print("  ✓ Inventory categories cleared")
    
    # 6. Clear vendors
    print("[6/7] Clearing vendors...")
    db.execute(text("DELETE FROM vendors"))
    print("  ✓ Vendors cleared")
    
    # 7. Clear locations (except rooms)
    print("[7/7] Clearing inventory locations (preserving guest rooms)...")
    db.execute(text("DELETE FROM locations WHERE location_type != 'GUEST_ROOM'"))
    result = db.execute(text("SELECT COUNT(*) FROM locations"))
    remaining = result.fetchone()[0]
    print(f"  ✓ Inventory locations cleared ({remaining} guest rooms preserved)")
    
    # Commit all changes
    db.commit()
    
    print("\n" + "=" * 80)
    print("✓ ALL INVENTORY MASTER DATA CLEARED SUCCESSFULLY!")
    print("=" * 80)
    print("\nAll inventory items, categories, vendors, and locations have been removed.")
    print("Guest room locations have been preserved.")
    print("\nYou can now:")
    print("  - Create new inventory categories")
    print("  - Add new vendors")
    print("  - Create new inventory items")
    print("  - Set up new inventory locations")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
    print("\nChanges rolled back. Database unchanged.")
finally:
    db.close()
