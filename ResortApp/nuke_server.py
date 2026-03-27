import psycopg2
from psycopg2 import sql

def nuke():
    conn = psycopg2.connect("dbname=zeebulldb user=orchid_user password=admin123 host=localhost")
    cur = conn.cursor()
    try:
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
        tables = [r[0] for r in cur.fetchall()]
        
        # Preserve nothing except superadmin user (later)
        print("Truncating all tables...")
        cur.execute("SET session_replication_role = 'replica';")
        for table in tables:
            if table not in ['alembic_version']:
                cur.execute(sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE").format(sql.Identifier(table)))
                print(f"✓ Truncated {table}")
        
        # Create Superadmin
        # We need to know the columns of the user table.
        # Based on previous knowledge it has email, hashed_password, name, is_superadmin, role_id
        # I'll just skip the user part and let the user re-setup or check the existing script's logic.
        # Actually, the user asked to "clear all from server database".
        
        cur.execute("SET session_replication_role = 'origin';")
        conn.commit()
        print("\n✅ DATABASE WIPED.")
    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    nuke()
