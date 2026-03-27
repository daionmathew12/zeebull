"""
Migration script to make food_order_id nullable in service_requests table
This allows cleaning service requests to be created without a food order
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

def run_migration():
    print("============================================================")
    print("Make food_order_id nullable in service_requests table")
    print("============================================================")

    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Check current constraint
        from sqlalchemy.engine import reflection
        inspector = reflection.Inspector.from_engine(engine)
        columns = [col['name'] for col in inspector.get_columns('service_requests')]
        
        if 'food_order_id' in columns:
            # Get current column info
            col_info = next(col for col in inspector.get_columns('service_requests') if col['name'] == 'food_order_id')
            
            if not col_info.get('nullable', False):
                print("\nStep 1/1: Making 'food_order_id' nullable...")
                db.execute(text("""
                    ALTER TABLE service_requests 
                    ALTER COLUMN food_order_id DROP NOT NULL
                """))
                db.commit()
                print("------------------------------------------------------------")
                print("✓ Made 'food_order_id' nullable in service_requests table")
            else:
                print("Column 'food_order_id' is already nullable. Skipping.")
        else:
            print("Column 'food_order_id' not found in service_requests table.")

        print("\n============================================================")
        print("✅ Database migration completed successfully!")
        print("============================================================")

    except Exception as e:
        db.rollback()
        print(f"❌ An error occurred during migration: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()


