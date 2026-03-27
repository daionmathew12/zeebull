import os
from sqlalchemy import create_engine, text

candidates = [
    "postgresql://postgres:postgres@localhost:5432/orchid",
    "postgresql://postgres:password@localhost:5432/orchid",
    "postgresql://orchid:orchid@localhost:5432/orchid",
    "postgresql://postgres@localhost:5432/orchid",
    "postgresql://basilabrahamaby@localhost:5432/orchid",
    "sqlite:///./orchid.db",
    "sqlite:///../orchid.db"
]

def check_dbs():
    for url in candidates:
        print(f"Trying {url} ...")
        try:
            engine = create_engine(url)
            with engine.connect() as conn:
                print(f"  ✅ Connected!")
                
                # Check tables
                try:
                    if "sqlite" in url:
                        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='employees'"))
                    else:
                        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_name = 'employees'"))
                    
                    if result.first():
                        print("  ✅ 'employees' table exists")
                        
                        # Check columns
                        if "sqlite" in url:
                            cols = conn.execute(text("PRAGMA table_info(employees)")).fetchall()
                            col_names = [c[1] for c in cols]
                        else:
                            cols = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'employees'")).fetchall()
                            col_names = [c[0] for c in cols]
                            
                        print(f"  Columns: {col_names}")
                        if 'user_id' in col_names:
                             print("  ✅ user_id column present")
                        else:
                             print("  ❌ user_id column MISSING")
                             
                        if 'salary_payments' in col_names or 'salary_payments' in [t[0] for t in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'" if "sqlite" in url else "SELECT table_name FROM information_schema.tables")).fetchall()]:
                             print("  ✅ salary_payments table exists")
                    else:
                        print("  ❌ 'employees' table NOT found")
                except Exception as e:
                    print(f"  ⚠️ Error checking schema: {e}")
                    
        except Exception as e:
            print(f"  ❌ Failed to connect: {e}")

if __name__ == "__main__":
    check_dbs()
