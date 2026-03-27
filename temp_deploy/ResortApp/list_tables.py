
from app.database import SessionLocal
from sqlalchemy import text

def list_all_tables():
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"))
        tables = [row[0] for row in result]
        print("\nAll Tables in Database:")
        for t in tables:
            print(f"  - {t}")
            
        # Also count rows in each table to see what's left
        print("\nTable Row Counts:")
        for t in tables:
            try:
                count_res = db.execute(text(f"SELECT COUNT(*) FROM {t}"))
                count = count_res.fetchone()[0]
                if count > 0:
                    print(f"  {t}: {count}")
            except:
                pass
    finally:
        db.close()

if __name__ == "__main__":
    list_all_tables()
