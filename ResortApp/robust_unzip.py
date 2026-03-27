import zipfile
import os
import sys

def extract_zip(zip_path, target_dir):
    print(f"Extracting {zip_path} to {target_dir}...")
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
        
    with zipfile.ZipFile(zip_path, 'r') as z:
        for f in z.namelist():
            # Standardize path separators
            new_path = f.replace('\\', '/')
            
            # Remove leading folder if it exists (like "build/")
            if '/' in new_path:
                parts = new_path.split('/')
                if parts[0] == 'build':
                    new_path = '/'.join(parts[1:])
            
            if not new_path:
                continue
                
            full_path = os.path.join(target_dir, new_path)
            
            if f.endswith('\\') or f.endswith('/'):
                os.makedirs(full_path, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'wb') as out:
                    out.write(z.read(f))
    print("Done.")

if __name__ == "__main__":
    extract_zip("/home/basilabrahamaby/dashboard_deploy.zip", "/var/www/zeebull/dasboard/build/")
    extract_zip("/home/basilabrahamaby/userend_deploy.zip", "/var/www/zeebull/userend/build/")
