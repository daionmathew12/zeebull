
import os

root_dir = r"C:\releasing\New Orchid\ResortApp\app"

print("Scanning app directory...")

for dirpath, dirnames, filenames in os.walk(root_dir):
    for filename in filenames:
        if filename.endswith(".py"):
            file_path = os.path.join(dirpath, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Replace the symbol
                if '₹' in content:
                    print(f"Found symbol in {file_path}") # SAFE PRINT
                    new_content = content.replace('₹', 'Rs.')
                    new_content = new_content.replace('✅', '[OK]')
                    new_content = new_content.replace('❌', '[ERROR]')
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"  [FIXED] Sanitized {filename}")
                elif '✅' in content or '❌' in content:
                     print(f"Found emojis in {file_path}")
                     new_content = content.replace('✅', '[OK]')
                     new_content = content.replace('❌', '[ERROR]')
                     with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                     print(f"  [FIXED] Sanitized Emojis in {filename}")

            except Exception as e:
                print(f"Error processing {file_path}: {e}")

print("Sanitization Complete.")
