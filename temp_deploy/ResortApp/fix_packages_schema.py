from sqlalchemy import create_engine, text

# Database connection for Orchid server
DATABASE_URL = "postgresql://orchid_user:admin123@localhost/orchid_resort"

def add_missing_columns():
    """Add missing columns to packages table"""
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            print("=== ADDING MISSING COLUMNS TO PACKAGES TABLE ===\n")
            
            # Check if status column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'packages' AND column_name = 'status'
            """))
            
            if not result.fetchone():
                print("📝 Adding 'status' column...")
                conn.execute(text("""
                    ALTER TABLE packages 
                    ADD COLUMN status VARCHAR DEFAULT 'active'
                """))
                print("   ✅ Added 'status' column")
            else:
                print("   ℹ️  'status' column already exists")
            
            # Check and add other potentially missing columns
            columns_to_add = [
                ("theme", "VARCHAR", "NULL"),
                ("default_adults", "INTEGER", "2"),
                ("default_children", "INTEGER", "0"),
                ("max_stay_days", "INTEGER", "NULL"),
                ("food_included", "VARCHAR", "NULL"),
                ("food_timing", "VARCHAR", "NULL"),
                ("complimentary", "VARCHAR", "NULL"),
            ]
            
            for col_name, col_type, col_default in columns_to_add:
                result = conn.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'packages' AND column_name = '{col_name}'
                """))
                
                if not result.fetchone():
                    print(f"📝 Adding '{col_name}' column...")
                    if col_default == "NULL":
                        conn.execute(text(f"""
                            ALTER TABLE packages 
                            ADD COLUMN {col_name} {col_type}
                        """))
                    else:
                        conn.execute(text(f"""
                            ALTER TABLE packages 
                            ADD COLUMN {col_name} {col_type} DEFAULT {col_default}
                        """))
                    print(f"   ✅ Added '{col_name}' column")
                else:
                    print(f"   ℹ️  '{col_name}' column already exists")
            
            conn.commit()
            
            print("\n✅ MIGRATION COMPLETE!")
            
            # Show final schema
            print("\n=== FINAL PACKAGES TABLE SCHEMA ===")
            result = conn.execute(text("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns 
                WHERE table_name = 'packages' 
                ORDER BY ordinal_position
            """))
            
            for row in result:
                print(f"  {row[0]}: {row[1]} (default: {row[2]})")
            
        except Exception as e:
            conn.rollback()
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    add_missing_columns()
