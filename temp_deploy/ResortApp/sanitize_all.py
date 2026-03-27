
import os

root_dir = r"C:\releasing\New Orchid\ResortApp\app"

print(f"Scanning {root_dir}...")

for dirpath, dirnames, filenames in os.walk(root_dir):
    for filename in filenames:
        if filename.endswith(".py"):
            file_path = os.path.join(dirpath, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Replace the symbol
                if '₹' in content:
                    print(f"Found '₹' in {file_path}")
                    new_content = content.replace('₹', 'Rs.')
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"  [FIXED] Replaced '₹' with 'Rs.'")
                else:
                    pass
                    
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

# Also check root folder files just in case
root_files = [
    r"C:\releasing\New Orchid\ResortApp\checkout.py",
     r"C:\releasing\New Orchid\ResortApp\app\main.py" 
]
for file_path in root_files:
    if os.path.exists(file_path):
        try:
             with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
             if '₹' in content:
                print(f"Found '₹' in {file_path}")
                new_content = content.replace('₹', 'Rs.')
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"  [FIXED] Replaced '₹' with 'Rs.'")
        except Exception as e:
            print(f"Error {file_path}: {e}")

print("Sanitization Complete.")
