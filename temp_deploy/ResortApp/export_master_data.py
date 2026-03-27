import json
from app.database import get_db
from sqlalchemy import text

def export_master_data():
    """Export inventory items, categories, vendors, and location stocks"""
    db = next(get_db())
    
    data = {
        'inventory_categories': [],
        'inventory_items': [],
        'vendors': [],
        'locations': [],
        'location_stocks': []
    }
    
    # Export Categories
    categories = db.execute(text("""
        SELECT * FROM inventory_categories ORDER BY id
    """)).fetchall()
    
    cat_cols = db.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'inventory_categories' ORDER BY ordinal_position
    """)).fetchall()
    cat_col_names = [c[0] for c in cat_cols]
    
    for cat in categories:
        cat_dict = {}
        for i, col_name in enumerate(cat_col_names):
            val = cat[i]
            if hasattr(val, 'isoformat'):
                val = val.isoformat()
            cat_dict[col_name] = val
        data['inventory_categories'].append(cat_dict)
    
    # Export Inventory Items
    items = db.execute(text("""
        SELECT * FROM inventory_items ORDER BY id
    """)).fetchall()
    
    item_cols = db.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'inventory_items' ORDER BY ordinal_position
    """)).fetchall()
    item_col_names = [c[0] for c in item_cols]
    
    for item in items:
        item_dict = {}
        for i, col_name in enumerate(item_col_names):
            val = item[i]
            if hasattr(val, 'isoformat'):
                val = val.isoformat()
            elif isinstance(val, (int, float)):
                val = float(val) if '.' in str(val) or 'price' in col_name or 'percentage' in col_name else val
            item_dict[col_name] = val
        data['inventory_items'].append(item_dict)
    
    # Export Vendors
    vendors = db.execute(text("""
        SELECT * FROM vendors ORDER BY id
    """)).fetchall()
    
    vendor_cols = db.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'vendors' ORDER BY ordinal_position
    """)).fetchall()
    vendor_col_names = [c[0] for c in vendor_cols]
    
    for vendor in vendors:
        vendor_dict = {}
        for i, col_name in enumerate(vendor_col_names):
            val = vendor[i]
            if hasattr(val, 'isoformat'):
                val = val.isoformat()
            vendor_dict[col_name] = val
        data['vendors'].append(vendor_dict)
    
    # Export Locations
    locations = db.execute(text("""
        SELECT * FROM locations ORDER BY id
    """)).fetchall()
    
    loc_cols = db.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'locations' ORDER BY ordinal_position
    """)).fetchall()
    loc_col_names = [c[0] for c in loc_cols]
    
    for loc in locations:
        loc_dict = {}
        for i, col_name in enumerate(loc_col_names):
            val = loc[i]
            if hasattr(val, 'isoformat'):
                val = val.isoformat()
            loc_dict[col_name] = val
        data['locations'].append(loc_dict)
    
    # Export Location Stocks
    stocks = db.execute(text("""
        SELECT * FROM location_stocks ORDER BY id
    """)).fetchall()
    
    stock_cols = db.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'location_stocks' ORDER BY ordinal_position
    """)).fetchall()
    stock_col_names = [c[0] for c in stock_cols]
    
    for stock in stocks:
        stock_dict = {}
        for i, col_name in enumerate(stock_col_names):
            val = stock[i]
            if hasattr(val, 'isoformat'):
                val = val.isoformat()
            elif isinstance(val, (int, float)):
                val = float(val)
            stock_dict[col_name] = val
        data['location_stocks'].append(stock_dict)
    
    # Save to JSON file
    with open('master_data_export.json', 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f"✅ Exported:")
    print(f"  - {len(data['inventory_categories'])} Categories")
    print(f"  - {len(data['inventory_items'])} Inventory Items")
    print(f"  - {len(data['vendors'])} Vendors")
    print(f"  - {len(data['locations'])} Locations")
    print(f"  - {len(data['location_stocks'])} Location Stocks")
    print(f"\n📁 Saved to: master_data_export.json")

if __name__ == "__main__":
    export_master_data()
