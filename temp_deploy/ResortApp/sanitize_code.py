import os

# List of files identified by grep as containing the symbol
files_to_check = [
    r"C:\releasing\New Orchid\ResortApp\app\utils\accounting_helpers.py",
    r"C:\releasing\New Orchid\ResortApp\app\api\dashboard.py",
    r"C:\releasing\New Orchid\ResortApp\app\utils\pdf_generator.py",
    r"C:\releasing\New Orchid\ResortApp\app\curd\notification.py",
    r"C:\releasing\New Orchid\ResortApp\app\curd\account.py",
    r"C:\releasing\New Orchid\ResortApp\app\api\gst_reports.py"
]

for file_path in files_to_check:
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace the symbol
            new_content = content.replace('₹', 'Rs.')
            
            if content != new_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Sanitized: {file_path}")
            else:
                print(f"No changes needed: {file_path}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    else:
        print(f"File not found: {file_path}")
