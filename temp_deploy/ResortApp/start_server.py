import os
import subprocess
import sys

def start():
    print("Searching for .env...")
    env_path = None
    db_url = None
    
    # search in current and home
    search_dirs = [os.getcwd(), "/home/basilabrahamaby"]
    
    for start_dir in search_dirs:
        for root, dirs, files in os.walk(start_dir):
            if ".env" in files:
                full = os.path.join(root, ".env")
                print(f"Found .env at: {full}")
                try:
                    with open(full, 'r') as f:
                        for line in f:
                            if "DATABASE_URL" in line:
                                db_url = line.strip().split("=", 1)[1]
                                print(f"Found DB URL: {db_url}")
                                env_path = full
                                break
                except:
                    pass
            if db_url: break
        if db_url: break

    if not db_url:
        print("❌ Could not find DATABASE_URL in any .env")
        # create valid default one if I know it
        # db_url = "postgresql+psycopg2://orchid_resort_user:admin123@localhost/orchid_resort_db"
        # print(f"Using fallback: {db_url}")
        sys.exit(1)

    # Set env var
    env = os.environ.copy()
    env["DATABASE_URL"] = db_url

    print("Starting uvicorn...")
    # Run uvicorn
    # uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    # Assume main.py is in current dir, so "main:app"
    cmd = [sys.executable, "main.py"] 
    # OR python -m uvicorn main:app ...
    
    # Since main.py has uvicorn.run(), just running python main.py is fine.
    subprocess.run([sys.executable, "main.py"], env=env)

if __name__ == "__main__":
    start()
