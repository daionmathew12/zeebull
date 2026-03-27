"""
Clear Waste Logs Only
"""

from app.database import SessionLocal
from sqlalchemy import text

def clear_waste_logs():
    """Clear only waste logs"""
    
    db = SessionLocal()
    try:
        print("🧹 Clearing waste logs...")
        
        result = db.execute(text("DELETE FROM waste_logs"))
        rows = result.rowcount
        
        db.commit()
        
        if rows > 0:
            print(f"✅ Cleared {rows} waste log(s)")
        else:
            print("✅ Waste logs table is already empty")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Error clearing waste logs: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    clear_waste_logs()
