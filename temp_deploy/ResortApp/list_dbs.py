
from sqlalchemy import create_engine, text

def list_databases():
    # Try connecting to postgres default db
    try:
        engine = create_engine("postgresql://postgres:qwerty123@localhost:5432/postgres")
        with engine.connect() as conn:
            # We need to use conn.execute(text(...)) outside a transaction for some things, 
            # but for SELECT it's fine.
            # postgresql list dbs:
            res = conn.execute(text("SELECT datname FROM pg_database WHERE datistemplate = false"))
            dbs = [r[0] for r in res]
            print("Databases found:")
            for db in dbs:
                print(f"  - {db}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_databases()
