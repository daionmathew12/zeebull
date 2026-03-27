import os

def read_env():
    path = "/home/basilabrahamaby/orchid-repo/ResortApp/.env"
    print(f"Reading {path}...")
    try:
        with open(path, 'r') as f:
            content = f.read()
            print("--- CONTENT START ---")
            print(content)
            print("--- CONTENT END ---")
    except Exception as e:
        print(f"Error: {e}")
        
    # Also search again just in case
    for root, dirs, files in os.walk("/home/basilabrahamaby"):
        if ".env" in files:
            full = os.path.join(root, ".env")
            print(f"Found: {full}")
            try:
                with open(full, 'r') as f:
                    print(f"  Content of {full}:")
                    print(f.read())
            except:
                pass

if __name__ == "__main__":
    read_env()
