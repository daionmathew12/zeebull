#!/usr/bin/env python3
"""
Reset all inventory stock to zero
"""

from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

try:
    print("🔄 Resetting all inventory stock to 0...")
    print("=" * 60)
    
    # Reset all location stocks to 0
    result = db.execute(text("UPDATE location_stocks SET quantity = 0, last_updated = NOW()"))
    rows_affected = result.rowcount
    
    db.commit()
    
    print(f"✅ Reset {rows_affected} location stock records to 0")
    print("=" * 60)
    
    # Verify
    verify = db.execute(text("SELECT COUNT(*) as total, SUM(quantity) as total_qty FROM location_stocks"))
    row = verify.fetchone()
    
    print(f"\n📊 Verification:")
    print(f"   Total location stock records: {row[0]}")
    print(f"   Total quantity across all locations: {row[1]}")
    
    if row[1] == 0:
        print("\n✅ All stock successfully reset to 0!")
    else:
        print(f"\n⚠️  Warning: Total quantity is {row[1]}, expected 0")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    db.rollback()
finally:
    db.close()
