import os
import zipfile

def zip_dir(path, zip_handle, exclude_dirs=None, exclude_files=None):
    if exclude_dirs is None:
        exclude_dirs = []
    if exclude_files is None:
        exclude_files = []
    
    for root, dirs, files in os.walk(path):
        # Exclude directories
        to_keep = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
        dirs.clear()
        dirs.extend(to_keep)
        
        for file in files:
            is_excluded = False
            if file.startswith('.'):
                is_excluded = True
            for ex in exclude_files:
                if file == ex:
                    is_excluded = True
                    break
            
            if is_excluded:
                continue
            
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, path)
            zip_handle.write(file_path, rel_path)

def create_bundles():
    print("Creating bundles...")
    
    # 1. Backend Bundle (ResortApp)
    backend_zip = 'zeebull_backend.zip'
    with zipfile.ZipFile(backend_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zip_dir('ResortApp', zipf, exclude_dirs=['venv', '__pycache__', 'uploads', 'static', 'tests'], exclude_files=['.env', 'orchid.db'])
    print(f"Created {backend_zip}")

    # 2. Admin Dashboard Bundle (dasboard/build)
    admin_zip = 'zeebull_admin.zip'
    if os.path.exists('dasboard/build'):
        with zipfile.ZipFile(admin_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zip_dir('dasboard/build', zipf)
        print(f"Created {admin_zip}")
    else:
        print("Warning: dasboard/build not found!")

    # 3. User End Bundle (userend/build)
    user_zip = 'zeebull_userend.zip'
    if os.path.exists('userend/build'):
        with zipfile.ZipFile(user_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zip_dir('userend/build', zipf)
        print(f"Created {user_zip}")
    else:
        print("Warning: userend/build not found!")

if __name__ == "__main__":
    create_bundles()
