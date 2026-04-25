import zipfile
import os

zip_path = '/home/basilabrahamsby/zeebull_backend_full.zip'
dest_path = '/var/www/teqmates/ResortApp'

print(f"Extracting {zip_path} to {dest_path}...")

with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    for member in zip_ref.infolist():
        # Normalize path: replace backslashes and ensure linux-style paths
        filename = member.filename.replace('\\', '/')
        target_path = os.path.join(dest_path, filename)
        
        if filename.endswith('/'):
            os.makedirs(target_path, exist_ok=True)
            continue
            
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # Extract file
        with open(target_path, 'wb') as f:
            f.write(zip_ref.read(member))
            
print("Extraction complete!")
