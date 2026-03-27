import os
import socket
from sqlalchemy import create_engine, text

def check_port(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(2)
        return s.connect_ex((host, port)) == 0

def find_env_files():
    print("Searching for .env files...")
    start_dir = "/home/basilabrahamaby"
    for root, dirs, files in os.walk(start_dir):
        if ".env" in files:
            print(f"  Found: {os.path.join(root, '.env')}")
            # Try to read it
            try:
                with open(os.path.join(root, '.env'), 'r') as f:
                    content = f.read()
                    for line in content.splitlines():
                        if "DATABASE_URL" in line:
                            print(f"    --> {line}")
            except Exception as e:
                print(f"    Error reading: {e}")

def check_dbs():
    print(f"Checking Postgres port 5432: {'OPEN' if check_port('localhost', 5432) else 'CLOSED'}")
    
    candidates = [
        "postgresql://postgres:postgres@localhost:5432/orchid",
        "postgresql://postgres:password@localhost:5432/orchid",
        "postgresql://orchid:orchid@localhost:5432/orchid",
        "postgresql://basilabrahamaby:password@localhost:5432/orchid",
        "postgresql://basilabrahamaby@localhost:5432/orchid",
        "postgresql://postgres:123456@localhost:5432/orchid",
        "postgresql://orchid_user:orchid_pass@localhost:5432/orchid"
    ]

    for url in candidates:
        print(f"Trying {url} ...")
        try:
            engine = create_engine(url)
            with engine.connect() as conn:
                print(f"  ✅ Connected!")
                return url
        except Exception as e:
             pass # Silently fail for cleaner output or print short error
             # print(f"  ❌ {e}")

    return None

if __name__ == "__main__":
    find_env_files()
    valid_url = check_dbs()
    if valid_url:
        print(f"\n✅ VALID DATABASE FOUND: {valid_url}")
    else:
        print("\n❌ Could not connect to any Postgres database.")
