from app.database import SessionLocal
from sqlalchemy import text

def migrate_v2():
    db = SessionLocal()
    try:
        def add_column(table, column, type_def):
            check_sql = text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}' AND column_name='{column}'")
            result = db.execute(check_sql).fetchone()
            if not result:
                print(f"Adding {column} to {table}...")
                db.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {type_def}"))
                db.commit()
                print(f"✓ Successfully added '{column}' to {table}")
            else:
                print(f"- Column '{column}' already exists in {table}")

        # Table: employees
        print("Migrating 'employees' table...")
        add_column('employees', 'daily_tasks', 'TEXT')
        
        # Table: working_logs
        print("Migrating 'working_logs' table...")
        add_column('working_logs', 'completed_tasks', 'TEXT')
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_v2()
