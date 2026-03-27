import zipfile
import os
import shutil

zips = [
    ("~/backend_wipe.zip", "/var/www/zeebull/ResortApp"),
    ("~/dashboard_wipe.zip", "/var/www/zeebull/dashboard"),
    ("~/userend_wipe.zip", "/var/www/zeebull/userend")
]

def safe_extract(zip_path, target_dir):
    with zipfile.ZipFile(zip_path, 'r') as z:
        for member in z.infolist():
            # Replace backslashes with forward slashes
            path = member.filename.replace('\\', '/')
            # Ensure target path is valid
            target_path = os.path.join(target_dir, path)
            
            if member.is_dir() or path.endswith('/'):
                if not os.path.exists(target_path):
                    os.makedirs(target_path, exist_ok=True)
                continue
            
            # Ensure parent directory exists
            parent = os.path.dirname(target_path)
            if not os.path.exists(parent):
                os.makedirs(parent, exist_ok=True)
            
            # Extract file
            try:
                with z.open(member) as source, open(target_path, "wb") as target:
                    shutil.copyfileobj(source, target)
            except Exception as e:
                print(f"Error extracting {path}: {e}")

for zip_rel_path, target_dir in zips:
    zip_path = os.path.expanduser(zip_rel_path)
    if not os.path.exists(zip_path):
        print(f"SKIP: {zip_path} not found.")
        continue

    print(f"Extracting {zip_path} to {target_dir}...")
    
    # Backup .env if it exists
    env_file = os.path.join(target_dir, ".env")
    has_env = os.path.exists(env_file)
    if has_env:
         shutil.copy(env_file, "/tmp/.env.bak")
         print("Backed up .env")

    # Wipe and recreate
    if os.path.exists(target_dir):
        # We don't rmtree ResortApp because of venv
        if "ResortApp" in target_dir:
            for item in os.listdir(target_dir):
                if item == "venv": continue
                path = os.path.join(target_dir, item)
                if os.path.isfile(path) or os.path.islink(path):
                    os.unlink(path)
                else:
                    shutil.rmtree(path)
        else:
            shutil.rmtree(target_dir)

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    safe_extract(zip_path, target_dir)
    
    # Restore .env
    if has_env:
        shutil.move("/tmp/.env.bak", env_file)
        print("Restored .env")
    
    print(f"✓ {zip_path} extracted.")

# Symlink dasboard to dashboard
if os.path.exists("/var/www/zeebull/dashboard"):
    if os.path.exists("/var/www/zeebull/dasboard"):
        if not os.path.islink("/var/www/zeebull/dasboard"):
            os.system("sudo rm -rf /var/www/zeebull/dasboard")
    os.system("sudo ln -s /var/www/zeebull/dashboard /var/www/zeebull/dasboard")

# Fix permissions
os.system("sudo chown -R basilabrahamaby:www-data /var/www/zeebull")
os.system("sudo chmod -R 775 /var/www/zeebull")
os.system("sudo systemctl restart zeebull.service")
print("Full fix complete.")
