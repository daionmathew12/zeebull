from app.database import engine
from sqlalchemy import text

def fix_table():
    with engine.connect() as conn:
        print("Starting table fix for 'expenses'...")
        
        # Columns to add
        cols = [
            ("department", "VARCHAR"),
            ("status", "VARCHAR DEFAULT 'Pending'"),
            ("rcm_applicable", "BOOLEAN DEFAULT FALSE"),
            ("rcm_tax_rate", "FLOAT"),
            ("nature_of_supply", "VARCHAR"),
            ("original_bill_no", "VARCHAR"),
            ("self_invoice_number", "VARCHAR"),
            ("vendor_id", "INTEGER"),
            ("rcm_liability_date", "DATE"),
            ("itc_eligible", "BOOLEAN DEFAULT TRUE")
        ]
        
        for col_name, col_type in cols:
            print(f"Adding column {col_name} if not exists...")
            try:
                # PostgreSQL-specific check for column existence
                query = text(f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                   WHERE table_name='expenses' AND column_name='{col_name}') THEN
                        ALTER TABLE expenses ADD COLUMN {col_name} {col_type};
                    END IF;
                END $$;
                """)
                conn.execute(query)
                conn.commit()
                print(f"  Processed {col_name}")
            except Exception as e:
                print(f"  Error adding {col_name}: {e}")
        
        print("Table fix completed!")

if __name__ == "__main__":
    fix_table()
