"""
Clear All Services
This script removes all services and their related data.
"""
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    print("=" * 80)
    print("CLEARING ALL SERVICES")
    print("=" * 80)
    print("\nThis will delete:")
    print("  - All services")
    print("  - All service images")
    print("  - All service inventory items")
    print("  - All laundry services")
    print("=" * 80)
    
    # Confirm
    response = input("\nAre you sure you want to proceed? (type 'YES' to confirm): ")
    if response != "YES":
        print("Operation cancelled.")
        db.close()
        exit()
    
    print("\nStarting cleanup...")
    
    # 1. Clear service images
    print("\n[1/4] Clearing service images...")
    db.execute(text("DELETE FROM service_images"))
    print("  ✓ Service images cleared")
    
    # 2. Clear service inventory items
    print("[2/4] Clearing service inventory items...")
    db.execute(text("DELETE FROM service_inventory_items"))
    print("  ✓ Service inventory items cleared")
    
    # 3. Clear laundry services
    print("[3/4] Clearing laundry services...")
    db.execute(text("DELETE FROM laundry_services"))
    print("  ✓ Laundry services cleared")
    
    # 4. Clear services
    print("[4/4] Clearing services...")
    db.execute(text("DELETE FROM services"))
    print("  ✓ Services cleared")
    
    # Commit all changes
    db.commit()
    
    print("\n" + "=" * 80)
    print("✓ ALL SERVICES CLEARED SUCCESSFULLY!")
    print("=" * 80)
    print("\nAll services and related data have been removed.")
    print("You can now create new services from scratch.")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    db.rollback()
    print("Changes rolled back. Database unchanged.")
finally:
    db.close()
