"""
Fix locations table - Remove or make item_id nullable

This script checks if the locations table has an item_id column
and either removes it or makes it nullable.
"""
from app.database import SessionLocal, engine
from sqlalchemy import text

def fix_locations_table():
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("CHECKING LOCATIONS TABLE SCHEMA")
        print("=" * 70)
        
        # Check if item_id column exists in locations table
        result = db.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'locations'
            ORDER BY ordinal_position;
        """))
        
        columns = result.fetchall()
        
        print("\nColumns in locations table:")
        has_item_id = False
        for col in columns:
            print(f"  {col[0]}: {col[1]} (nullable: {col[2]})")
            if col[0] == 'item_id':
                has_item_id = True
                print(f"    ⚠️  Found item_id column! (nullable: {col[2]})")
        
        if has_item_id:
            print("\n" + "=" * 70)
            print("FIXING ISSUE: Making item_id nullable")
            print("=" * 70)
            
            # Make item_id nullable
            db.execute(text("""
                ALTER TABLE locations 
                ALTER COLUMN item_id DROP NOT NULL;
            """))
            db.commit()
            
            print("✅ Successfully made item_id nullable in locations table")
            print("\nYou can now try creating the asset mapping again.")
        else:
            print("\n✅ No item_id column found in locations table")
            print("The issue might be elsewhere. Check the error message again.")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    fix_locations_table()
