import os
import re

def find_all_require_permission():
    pattern = re.compile(r'require_permission\((.*?)\)')
    for root, dirs, files in os.walk("."):
        if "venv" in root or ".git" in root or "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    matches = pattern.findall(content)
                    if matches:
                        print(f"File: {path}")
                        for m in matches:
                            print(f"  - {m}")

if __name__ == "__main__":
    find_all_require_permission()
