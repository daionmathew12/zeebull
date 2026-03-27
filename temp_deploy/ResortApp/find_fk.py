import glob
import os

for f in glob.glob("app/models/*.py"):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
        if "ForeignKey(" in content:
            # Check if any import line has ForeignKey
            lines = content.split('\n')
            has_import = False
            for line in lines:
                if line.startswith('from sqlalchemy') and 'import' in line and 'ForeignKey' in line:
                    has_import = True
                    break
            if not has_import:
                print(f"MISSING ForeignKey: {f}")
