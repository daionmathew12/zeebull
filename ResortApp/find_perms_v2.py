import os
import re

def find_permissions():
    root_dir = "app"
    permissions = set()
    pattern = re.compile(r'require_permission\("([^"]+)"\)')
    pattern2 = re.compile(r"require_permission\('([^']+)'\)")

    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    try:
                        content = f.read()
                        matches = pattern.findall(content)
                        matches2 = pattern2.findall(content)
                        for m in matches + matches2:
                            permissions.add((m, path))
                    except:
                        pass
    
    print("Found permissions:")
    for p, path in sorted(permissions):
        print(f"  {p} (in {path})")

if __name__ == "__main__":
    find_permissions()
