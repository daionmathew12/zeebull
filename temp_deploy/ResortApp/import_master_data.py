import json
import sys
from sqlalchemy import create_engine, text

# Database connection for Orchid server
DATABASE_URL = "postgresql://orchid_user:admin123@localhost/orchid_resort"

def get_table_columns(conn, table_name):
    """Get list of columns for a table"""
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = :table_name
        ORDER BY ordinal_position
    """), {"table_name": table_name})
    return [row[0] for row in result]

def import_master_data(json_file='master_data_export.json'):
    """Import master data from JSON file"""
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            print("=== IMPORTING MASTER DATA ===\n")
            
            # Clear existing data first
            print("🗑️  Clearing existing data...")
            conn.execute(text("TRUNCATE TABLE location_stocks RESTART IDENTITY CASCADE"))
            conn.execute(text("TRUNCATE TABLE inventory_items RESTART IDENTITY CASCADE"))
            conn.execute(text("TRUNCATE TABLE inventory_categories RESTART IDENTITY CASCADE"))
            conn.execute(text("TRUNCATE TABLE vendors RESTART IDENTITY CASCADE"))
            conn.execute(text("TRUNCATE TABLE locations RESTART IDENTITY CASCADE"))
            conn.commit()
            print("   Done.\n")
            
            # Import Categories
            print(f"📦 Importing {len(data['inventory_categories'])} Categories...")
            cat_cols = get_table_columns(conn, 'inventory_categories')
            for cat in data['inventory_categories']:
                filtered_cat = {k: v for k, v in cat.items() if k in cat_cols}
                if filtered_cat:
                    cols = ', '.join([f'"{k}"' for k in filtered_cat.keys()])
                    placeholders = ', '.join([f':{k}' for k in filtered_cat.keys()])
                    query = f'INSERT INTO inventory_categories ({cols}) VALUES ({placeholders})'
                    conn.execute(text(query), filtered_cat)
            conn.commit()
            
            # Import Vendors
            print(f"🏢 Importing {len(data['vendors'])} Vendors...")
            vendor_cols = get_table_columns(conn, 'vendors')
            
            vendors_imported = 0
            for idx, vendor in enumerate(data['vendors']):
                try:
                    filtered_vendor = {k: v for k, v in vendor.items() if k in vendor_cols}
                    
                    if filtered_vendor:
                        cols = ', '.join([f'"{k}"' for k in filtered_vendor.keys()])
                        placeholders = ', '.join([f':{k}' for k in filtered_vendor.keys()])
                        query = f'INSERT INTO vendors ({cols}) VALUES ({placeholders})'
                        conn.execute(text(query), filtered_vendor)
                        conn.commit()
                        vendors_imported += 1
                except Exception as e:
                    conn.rollback()
                    print(f"   Warning: Skipping vendor '{vendor.get('name', 'unknown')}': {str(e)[:80]}")
            
            print(f"   Imported {vendors_imported}/{len(data['vendors'])} vendors")
            
            # Import Locations
            print(f"📍 Importing {len(data['locations'])} Locations...")
            loc_cols = get_table_columns(conn, 'locations')
            for loc in data['locations']:
                filtered_loc = {k: v for k, v in loc.items() if k in loc_cols}
                if filtered_loc:
                    cols = ', '.join([f'"{k}"' for k in filtered_loc.keys()])
                    placeholders = ', '.join([f':{k}' for k in filtered_loc.keys()])
                    query = f'INSERT INTO locations ({cols}) VALUES ({placeholders})'
                    conn.execute(text(query), filtered_loc)
            conn.commit()
            
            # Import Inventory Items
            print(f"📋 Importing {len(data['inventory_items'])} Inventory Items...")
            item_cols = get_table_columns(conn, 'inventory_items')
            for item in data['inventory_items']:
                filtered_item = {k: v for k, v in item.items() if k in item_cols}
                if filtered_item:
                    cols = ', '.join([f'"{k}"' for k in filtered_item.keys()])
                    placeholders = ', '.join([f':{k}' for k in filtered_item.keys()])
                    query = f'INSERT INTO inventory_items ({cols}) VALUES ({placeholders})'
                    conn.execute(text(query), filtered_item)
            conn.commit()
            
            # Import Location Stocks
            print(f"📊 Importing {len(data['location_stocks'])} Location Stocks...")
            stock_cols = get_table_columns(conn, 'location_stocks')
            for stock in data['location_stocks']:
                filtered_stock = {k: v for k, v in stock.items() if k in stock_cols}
                if filtered_stock:
                    cols = ', '.join([f'"{k}"' for k in filtered_stock.keys()])
                    placeholders = ', '.join([f':{k}' for k in filtered_stock.keys()])
                    query = f'INSERT INTO location_stocks ({cols}) VALUES ({placeholders})'
                    conn.execute(text(query), filtered_stock)
            conn.commit()
            
            # Update sequences
            print("\n🔄 Updating ID sequences...")
            tables = ['inventory_categories', 'inventory_items', 'vendors', 'locations', 'location_stocks']
            for table in tables:
                conn.execute(text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE((SELECT MAX(id) FROM {table}), 1))"))
            conn.commit()
            
            # Count what was actually imported
            cat_count = conn.execute(text("SELECT COUNT(*) FROM inventory_categories")).scalar()
            item_count = conn.execute(text("SELECT COUNT(*) FROM inventory_items")).scalar()
            vendor_count = conn.execute(text("SELECT COUNT(*) FROM vendors")).scalar()
            loc_count = conn.execute(text("SELECT COUNT(*) FROM locations")).scalar()
            stock_count = conn.execute(text("SELECT COUNT(*) FROM location_stocks")).scalar()
            
            print("\n✅ IMPORT COMPLETE!")
            print(f"  - {cat_count} Categories")
            print(f"  - {item_count} Inventory Items")
            print(f"  - {vendor_count} Vendors")
            print(f"  - {loc_count} Locations")
            print(f"  - {stock_count} Location Stocks")
            
        except Exception as e:
            conn.rollback()
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    import_master_data()
