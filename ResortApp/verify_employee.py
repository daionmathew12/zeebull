import os

def check_file():
    path = r"c:\releasing\New Orchid\ResortApp\app\api\employee.py"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        print(f"File length: {len(content)}")
        if "Depends" in content:
            print("Found 'Depends' in content")
            # Find all occurrences
            import re
            matches = re.findall(r'Depends\(.*?\)', content)
            for m in matches:
                print(f"  Match: {m}")
        else:
            print("'Depends' NOT found in content")

if __name__ == "__main__":
    check_file()
