#!/usr/bin/env python3
"""Create admin user for Orchid Resort"""

from app.database import SessionLocal
from app.models.user import User, Role
from passlib.context import CryptContext
from datetime import datetime

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
db = SessionLocal()

try:
    # Check if admin role exists
    admin_role = db.query(Role).filter(Role.name == 'Admin').first()
    if not admin_role:
        admin_role = Role(
            name='Admin',
            permissions='/dashboard,/bookings,/rooms,/services,/expenses,/food-orders,/food-categories,/food-items,/billing,/packages,/users,/roles,/employees,/reports,/account,/userfrontend_data,/guestprofiles,/employee-management'
        )
        db.add(admin_role)
        db.flush()
        print('Admin role created')
    else:
        print('Admin role already exists')
    
    # Check if admin user exists
    admin_user = db.query(User).filter(User.email == 'admin@orchid.com').first()
    if admin_user:
        # Update password
        admin_user.hashed_password = pwd_context.hash('admin123')
        print('Admin user password updated')
    else:
        # Create new admin user
        admin_user = User(
            name='Admin',
            email='admin@orchid.com',
            hashed_password=pwd_context.hash('admin123'),
            phone='1234567890',
            role_id=admin_role.id,
            is_active=True
        )
        db.add(admin_user)
        print('Admin user created')
    
    db.commit()
    print('\n=== Login Credentials ===')
    print('Email: admin@orchid.com')
    print('Password: admin123')
    print('========================\n')
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()

