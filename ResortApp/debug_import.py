
import os
import sys
print("Importing main...")
try:
    import main
    print("Import successful")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
