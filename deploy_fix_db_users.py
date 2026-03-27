import os
import psycopg2

def upgrade_schema():
    conn_params = "dbname=orchid_resort user=orchid_user password=admin123 host=localhost"
    try:
        conn = psycopg2.connect(conn_params)
        conn.autocommit = True
        cur = conn.cursor()
        
        tables = [
            "users",
            "roles"
        ]
        
        for table in tables:
            try:
                # Check if branch_id column exists
                cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}' and column_name='branch_id'")
                if not cur.fetchone():
                    cur.execute(f"ALTER TABLE {table} ADD COLUMN branch_id INTEGER REFERENCES branches(id)")
                    print(f"Added branch_id to {table}")
                else:
                    print(f"branch_id already exists in {table}")
            except Exception as e:
                print(f"Error on {table}: {e}")

        cur.close()
        conn.close()
        print("Schema update for users and roles complete.")
    except Exception as e:
        print("Failed to connect or update schema: ", e)

if __name__ == "__main__":
    upgrade_schema()
