import sqlite3
import os

# Database path
DB_PATH = 'c:/releasing/New Orchid/ResortApp/resort.db'

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Checking columns in working_logs...")
    cursor.execute("PRAGMA table_info(working_logs)")
    columns = [col[1] for col in cursor.fetchall()]

    new_columns = [
        ('clock_in_image', 'TEXT'),
        ('clock_out_image', 'TEXT')
    ]

    for col_name, col_type in new_columns:
        if col_name not in columns:
            print(f"Adding column {col_name} to working_logs...")
            try:
                cursor.execute(f"ALTER TABLE working_logs ADD COLUMN {col_name} {col_type}")
                print(f"Successfully added {col_name}")
            except Exception as e:
                print(f"Error adding {col_name}: {e}")
        else:
            print(f"Column {col_name} already exists.")

    conn.commit()
    conn.close()
    print("Migration completed.")

if __name__ == "__main__":
    migrate()
