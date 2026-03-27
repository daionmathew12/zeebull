from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://orchid_user:admin123@localhost/orchid_resort"

def get_ids():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("=== VALID IDS ===")
        # Get a food item
        food = conn.execute(text("SELECT id, name FROM food_items LIMIT 1")).fetchone()
        if food:
            print(f"FoodItem: {food[0]} ({food[1]})")
        else:
            print("❌ No Food items found")
            
        # Get an inventory item
        inv = conn.execute(text("SELECT id, name FROM inventory_items LIMIT 1")).fetchone()
        if inv:
            print(f"InventoryItem: {inv[0]} ({inv[1]})")
        else:
            print("❌ No Inventory items found")

if __name__ == "__main__":
    get_ids()
