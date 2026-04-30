import os

def search_everywhere():
    target = "employees:view"
    root_dir = "."
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    if target in f.read():
                        print(f"Found in: {path}")
            except:
                pass

if __name__ == "__main__":
    search_everywhere()
