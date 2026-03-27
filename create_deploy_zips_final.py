import zipfile
import os

def zip_dir(source_dir, output_filename, exclude_items=None):
    if exclude_items is None:
        exclude_items = []
    
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            # Prune excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_items]
            
            for file in files:
                if file in exclude_items:
                    continue
                
                full_path = os.path.join(root, file)
                # Create relative path for the zip, enforcing forward slashes
                rel_path = os.path.relpath(full_path, source_dir).replace('\\', '/')
                zipf.write(full_path, rel_path)

if __name__ == "__main__":
    print("Zipping Backend...")
    zip_dir('ResortApp', 'backend_deploy.zip', exclude_items=['venv', '__pycache__', '.git', '.env', '.idea', '.vscode'])
    
    print("Zipping Dashboard...")
    zip_dir('dasboard/build', 'dashboard_deploy.zip')
    
    print("Zipping Userend...")
    zip_dir('userend/build', 'userend_deploy.zip')
    
    print("Verification:")
    for f in ['backend_deploy.zip', 'dashboard_deploy.zip', 'userend_deploy.zip']:
        if os.path.exists(f):
            print(f"{f}: {os.path.getsize(f)} bytes")
