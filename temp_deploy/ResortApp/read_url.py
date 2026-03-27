import os

def read_env_clean():
    print("Walking to find .env...")
    for root, dirs, files in os.walk("/home/basilabrahamaby"):
        if ".env" in files:
            full = os.path.join(root, ".env")
            print(f"Found: {full}")
            try:
                with open(full, 'r') as f:
                    for line in f:
                        if "DATABASE_URL" in line:
                            print(f"URL: {line.strip()}")
            except Exception as e:
                print(f"Error reading {full}: {e}")

if __name__ == "__main__":
    read_env_clean()
