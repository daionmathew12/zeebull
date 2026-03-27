#!/usr/bin/env python3
"""Setup basic resort data for Orchid Resort"""

from app.database import SessionLocal
from app.models.frontend import ResortInfo
from datetime import datetime

db = SessionLocal()

try:
    # Check if resort info exists
    resort_info = db.query(ResortInfo).first()
    if not resort_info:
        resort_info = ResortInfo(
            name='Orchid Resort',
            address='123 Resort Lane, Paradise City, State 12345',
            facebook='https://facebook.com/orchidresort',
            instagram='https://instagram.com/orchidresort',
            twitter='https://twitter.com/orchidresort',
            linkedin='https://linkedin.com/company/orchidresort',
            is_active=True
        )
        db.add(resort_info)
        db.commit()
        print('✅ Basic resort info created')
    else:
        print('ℹ️  Resort info already exists')
    
    print('\n=== Orchid Resort Setup Complete ===')
    print(f'Resort Name: {resort_info.name}')
    print(f'Address: {resort_info.address}')
    print('====================================\n')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()

