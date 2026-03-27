import zipfile
import os

def zip_directory(path, zip_filename, root_folder_name=""):
    print(f"Creating {zip_filename}...")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(path):
            if '__pycache__' in root or 'node_modules' in root or '.git' in root or 'venv' in root:
                continue
            for file in files:
                if file.endswith('.pyc') or file == '.env':
                    continue
                
                file_path = os.path.join(root, file)
                # Ensure forward slashes for Linux compatibility
                if root_folder_name:
                    arcname = os.path.join(root_folder_name, os.path.relpath(file_path, path)).replace('\\', '/')
                else:
                    arcname = os.path.relpath(file_path, path).replace('\\', '/')
                zipf.write(file_path, arcname)
    print(f"Created {zip_filename}")

if __name__ == "__main__":
    # 1. Zip Userfrontend
    zip_directory('build', 'userend_deploy.zip', root_folder_name="")
    
    # 2. Zip Dashboard
    zip_directory('dasboard/build', 'dashboard_deploy.zip', root_folder_name="")
    
    # 3. Zip Backend
    zip_directory('ResortApp', 'backend_zeebull.zip', root_folder_name="ResortApp")
    
    # 4. Create Master Zip
    print("Creating zeebull_deploy_final.zip...")
    with zipfile.ZipFile('zeebull_deploy_final.zip', 'w', zipfile.ZIP_DEFLATED) as master_zip:
        # Add frontend (as userend/)
        master_zip.write('userend_deploy.zip', arcname='userend_deploy.zip')
        
        # Add dashboard (as dashboard/)
        master_zip.write('dashboard_deploy.zip', arcname='dashboard_deploy.zip')
        
        # Add backend
        # We'll just put the individual zips or folder structure? 
        # The deploy_zeebull_new.sh expects zeebull_deploy_final.zip to be unzipped to /var/www/zeebull/
        # AND it expects /var/www/zeebull/ResortApp to exist.
        
        # So let's just make one big zip with everything in the right place
    
    def create_master_zip():
        with zipfile.ZipFile('zeebull_deploy_final.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 1. Add Backend (in ResortApp/ folder)
            for root, dirs, files in os.walk('ResortApp'):
                if any(x in root for x in ['__pycache__', 'venv', '.git', 'storage', 'uploads', 'tmp']):
                    continue
                for file in files:
                    if file.endswith('.pyc') or file == '.env':
                        continue
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, '.').replace('\\', '/')
                    zipf.write(file_path, arcname)
            
            # Add migration script
            if os.path.exists('migrate_db_server.py'):
                zipf.write('migrate_db_server.py', arcname='ResortApp/migrate_db_server.py')
            
            # 2. Add Dashboard (in dashboard/ folder)
            for root, dirs, files in os.walk('dasboard/build'):
                for file in files:
                    file_path = os.path.join(root, file)
                    # We want this in dashboard/
                    rel = os.path.relpath(file_path, 'dasboard/build')
                    arcname = os.path.join('dashboard', rel).replace('\\', '/')
                    zipf.write(file_path, arcname)
            
            # 3. Add Userend (in userend/ folder)
            for root, dirs, files in os.walk('build'):
                for file in files:
                    file_path = os.path.join(root, file)
                    # We want this in userend/
                    rel = os.path.relpath(file_path, 'build')
                    arcname = os.path.join('userend', rel).replace('\\', '/')
                    zipf.write(file_path, arcname)
        print("Created zeebull_deploy_final.zip")

    create_master_zip()
