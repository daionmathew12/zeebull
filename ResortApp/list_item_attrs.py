
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from app.models.inventory import InventoryItem

def list_attributes():
    print(f"Attributes of InventoryItem:")
    for attr in dir(InventoryItem):
        if not attr.startswith('__'):
            print(f" - {attr}")
            
if __name__ == "__main__":
    list_attributes()
