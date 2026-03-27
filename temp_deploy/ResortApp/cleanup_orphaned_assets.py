"""
Cleanup script to deactivate orphaned asset mappings in checked-out rooms.
Run this to fix asset mappings that weren't deactivated when return services were completed.
"""
from app.database import SessionLocal
from app.models.inventory import AssetMapping
from app.models.room import Room
from sqlalchemy.orm import Session

def cleanup_orphaned_assets():
    """
    Find and deactivate asset mappings in rooms that are Available (checked out).
    These are orphaned assets that should have been deactivated during return service completion.
    """
    db = SessionLocal()
    try:
        # Find all Available rooms
        available_rooms = db.query(Room).filter(Room.status == "Available").all()
        
        total_deactivated = 0
        
        for room in available_rooms:
            if not room.inventory_location_id:
                continue
            
            # Find active asset mappings in this room
            active_mappings = db.query(AssetMapping).filter(
                AssetMapping.location_id == room.inventory_location_id,
                AssetMapping.is_active == True
            ).all()
            
            if active_mappings:
                print(f"\n[CLEANUP] Room {room.number} (Available) has {len(active_mappings)} active asset mappings:")
                
                for mapping in active_mappings:
                    # Deactivate the mapping
                    mapping.is_active = False
                    total_deactivated += 1
                    print(f"  - Deactivated: Item ID {mapping.item_id}")
        
        db.commit()
        print(f"\n✓ Cleanup complete! Deactivated {total_deactivated} orphaned asset mappings.")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting orphaned asset cleanup...")
    cleanup_orphaned_assets()
