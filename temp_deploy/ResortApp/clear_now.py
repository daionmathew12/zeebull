import os, sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path('.env'))
from sqlalchemy import create_engine, text

url = os.getenv('DATABASE_URL', '').replace('postgresql://', 'postgresql+psycopg2://', 1)
if not url:
    print('ERROR: No DATABASE_URL')
    sys.exit(1)

engine = create_engine(url)
with engine.connect() as conn:
    trans = conn.begin()
    try:
        print('Deleting assigned_services...')
        conn.execute(text('DELETE FROM assigned_services'))
        print('Deleting service_inventory_items...')
        conn.execute(text('DELETE FROM service_inventory_items'))
        print('Deleting service_images...')
        conn.execute(text('DELETE FROM service_images'))
        print('Deleting services...')
        conn.execute(text('DELETE FROM services'))
        trans.commit()
        print('SUCCESS: All cleared!')
    except Exception as e:
        trans.rollback()
        print(f'ERROR: {e}')
        raise



