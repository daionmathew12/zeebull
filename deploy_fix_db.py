import os
import psycopg2

def upgrade_schema():
    conn_params = "dbname=orchid_resort user=orchid_user password=admin123 host=localhost"
    try:
        conn = psycopg2.connect(conn_params)
        conn.autocommit = True
        cur = conn.cursor()
        
        tables = [
            "header_banner",
            "check_availability",
            "gallery",
            "reviews",
            "resort_info",
            "signature_experiences",
            "plan_weddings",
            "nearby_attractions",
            "nearby_attraction_banners"
        ]
        
        for table in tables:
            try:
                # Check if column exists
                cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}' and column_name='branch_id'")
                if not cur.fetchone():
                    cur.execute(f"ALTER TABLE {table} ADD COLUMN branch_id INTEGER REFERENCES branches(id)")
                    print(f"Added branch_id to {table}")
                else:
                    print(f"branch_id already exists in {table}")
            except Exception as e:
                print(f"Error on {table}: {e}")
                
        # Fix subtitle text column in header_banner if necessary
        try:
            cur.execute("ALTER TABLE header_banner ALTER COLUMN subtitle TYPE TEXT;")
        except Exception:
            pass
            
        # Fix map_link column in nearby_attractions and nearby_attraction_banners
        for table in ["nearby_attractions", "nearby_attraction_banners"]:
            try:
                cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}' and column_name='map_link'")
                if not cur.fetchone():
                    cur.execute(f"ALTER TABLE {table} ADD COLUMN map_link VARCHAR(512)")
                    print(f"Added map_link to {table}")
                else:
                    print(f"map_link already exists in {table}")
            except Exception as e:
                pass


        cur.close()
        conn.close()
        print("Schema update complete.")
    except Exception as e:
        print("Failed to connect or update schema: ", e)

if __name__ == "__main__":
    upgrade_schema()
