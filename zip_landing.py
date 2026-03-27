import zipfile
import os

source_dir = r"C:\releasing\Pumaholidays\landingpage"
output_filename = r"c:\releasing\New Orchid\landingpage.zip"

with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, source_dir)
            zipf.write(file_path, arcname)

print(f"Zip created successfully at {output_filename}")
