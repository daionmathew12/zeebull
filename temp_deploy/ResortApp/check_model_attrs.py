
try:
    from app.models.inventory import InventoryItem
    print("Attributes of InventoryItem:")
    for attr in dir(InventoryItem):
        if not attr.startswith('_'):
            print(attr)
except Exception as e:
    print(f"Error: {e}")
