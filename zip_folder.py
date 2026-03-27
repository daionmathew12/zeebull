import zipfile
import os
import sys

def zip_dir(path, zip_filename):
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, path).replace('\\', '/')
                zipf.write(file_path, arcname)

if __name__ == "__main__":
    if len(sys.argv) == 3:
        zip_dir(sys.argv[1], sys.argv[2])
