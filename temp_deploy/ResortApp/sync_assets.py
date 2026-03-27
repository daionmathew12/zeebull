
import psycopg2

def sync_item_fixed_asset_flag():
    try:
        conn = psycopg2.connect("postgresql://postgres:qwerty123@localhost:5432/orchiddb")
        cur = conn.cursor()
        
        # Update items where category is_asset_fixed=True but item is_asset_fixed=False
        cur.execute("""
            UPDATE inventory_items 
            SET is_asset_fixed = true 
            WHERE category_id IN (SELECT id FROM inventory_categories WHERE is_asset_fixed = true)
            AND is_asset_fixed = false;
        """)
        print(f"Synced {cur.rowcount} items with their categories.")
        
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    sync_item_fixed_asset_flag()
