"""
Migration script to create accounting tables
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
    print("Create Accounting Tables Migration")
    print("============================================================")

    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Create account_groups table
        print("\nStep 1/4: Creating 'account_groups' table...")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS account_groups (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL UNIQUE,
                account_type VARCHAR NOT NULL,
                description TEXT,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        db.commit()
        print("✓ Created 'account_groups' table")

        # Create account_ledgers table
        print("\nStep 2/4: Creating 'account_ledgers' table...")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS account_ledgers (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL,
                code VARCHAR UNIQUE,
                group_id INTEGER NOT NULL REFERENCES account_groups(id),
                module VARCHAR,
                description TEXT,
                opening_balance FLOAT DEFAULT 0.0,
                balance_type VARCHAR NOT NULL DEFAULT 'debit',
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                tax_type VARCHAR,
                tax_rate FLOAT,
                bank_name VARCHAR,
                account_number VARCHAR,
                ifsc_code VARCHAR,
                branch_name VARCHAR,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        db.commit()
        print("✓ Created 'account_ledgers' table")

        # Create journal_entries table
        print("\nStep 3/4: Creating 'journal_entries' table...")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS journal_entries (
                id SERIAL PRIMARY KEY,
                entry_number VARCHAR NOT NULL UNIQUE,
                entry_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                reference_type VARCHAR,
                reference_id INTEGER,
                description TEXT NOT NULL,
                total_amount FLOAT NOT NULL,
                created_by INTEGER REFERENCES users(id),
                notes TEXT,
                is_reversed BOOLEAN DEFAULT FALSE,
                reversed_entry_id INTEGER REFERENCES journal_entries(id),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """))
        db.commit()
        print("✓ Created 'journal_entries' table")

        # Create journal_entry_lines table
        print("\nStep 4/4: Creating 'journal_entry_lines' table...")
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS journal_entry_lines (
                id SERIAL PRIMARY KEY,
                entry_id INTEGER NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
                debit_ledger_id INTEGER REFERENCES account_ledgers(id),
                credit_ledger_id INTEGER REFERENCES account_ledgers(id),
                amount FLOAT NOT NULL,
                description TEXT,
                line_number INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))
        db.commit()
        print("✓ Created 'journal_entry_lines' table")

        # Create indexes
        print("\nCreating indexes...")
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_account_ledgers_group_id ON account_ledgers(group_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_journal_entries_reference ON journal_entries(reference_type, reference_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_journal_entries_date ON journal_entries(entry_date)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_journal_entry_lines_entry_id ON journal_entry_lines(entry_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_journal_entry_lines_debit ON journal_entry_lines(debit_ledger_id)"))
        db.execute(text("CREATE INDEX IF NOT EXISTS idx_journal_entry_lines_credit ON journal_entry_lines(credit_ledger_id)"))
        db.commit()
        print("✓ Created indexes")

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


