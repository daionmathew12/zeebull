"""
Clear Database Script - Preserves Admin Login
Clears all transactional data while preserving admin credentials
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import SessionLocal
from app.models.user import User, Role
from app.models.room import Room
from datetime import datetime

def clear_database_keep_admin():
    """Clear all transactional data but keep admin user and configuration"""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("DATABASE CLEANUP - PRESERVING ADMIN LOGIN")
        print("=" * 60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Get admin user
        admin_user = db.query(User).filter(User.email == "admin@orchid.com").first()
        if admin_user:
            print(f"✓ Found admin: {admin_user.name} ({admin_user.email})")
        else:
            print("⚠ Warning: Admin user not found!")
        
        print("\n" + "-" * 60)
        print("CLEARING DATA")
        print("-" * 60)
        
        # Delete in correct order to avoid foreign key constraints
        tables = [
            # Level 1: Tables with no dependencies
            "notifications",
            
            # Level 2: Payment and checkout related
            "checkout_payments",
            "checkout_items",
            "employee_inventory_assignments",
            
            # Level 3: Checkouts
            "checkouts",
            
            # Level 4: Service and food orders
            "assigned_services",
            "food_orders",
            
            # Level 5: Bookings
            "package_booking_rooms",
            "package_bookings",
            "booking_rooms",
            "bookings",
            
            # Level 6: Packages and services
            "package_images",
            "packages",
            "service_images",
            "service_inventory_items",
            "services",
            
            # Level 7: Food items
            "food_items",
            "food_categories",
            
            # Level 8: Other tables
            "expenses",
            "payments",
            "suggestions",
            "service_requests",
            "journal_entries",
            "accounts",
        ]
        
        for table in tables:
            try:
                result = db.execute(text(f"DELETE FROM {table}"))
                if result.rowcount > 0:
                    print(f"✓ Cleared {result.rowcount:4d} from {table}")
                db.commit()  # Commit after each table
            except Exception as e:
                db.rollback()
                error_msg = str(e)
                if "does not exist" not in error_msg:
                    print(f"  ⚠ {table}: {error_msg[:80]}")
        
        # Clear employees (except admin)
        if admin_user:
            try:
                result = db.execute(
                    text(f"DELETE FROM employees WHERE user_id != {admin_user.id}")
                )
                db.commit()
                if result.rowcount > 0:
                    print(f"✓ Cleared {result.rowcount:4d} from employees (kept admin)")
            except Exception as e:
                db.rollback()
                print(f"  ⚠ employees: {str(e)[:80]}")
        
        # Reset room statuses
        try:
            result = db.execute(text("UPDATE rooms SET status = 'Available'"))
            db.commit()
            print(f"✓ Reset {result.rowcount:4d} rooms to Available")
        except Exception as e:
            db.rollback()
            print(f"  ⚠ rooms: {str(e)[:80]}")
        
        # Clear non-admin users
        if admin_user:
            guest_role = db.query(Role).filter(Role.name == "guest").first()
            try:
                if guest_role:
                    result = db.execute(
                        text(f"DELETE FROM users WHERE id != {admin_user.id} AND role_id != {guest_role.id}")
                    )
                else:
                    result = db.execute(
                        text(f"DELETE FROM users WHERE id != {admin_user.id}")
                    )
                db.commit()
                if result.rowcount > 0:
                    print(f"✓ Cleared {result.rowcount:4d} from users (kept admin)")
            except Exception as e:
                db.rollback()
                print(f"  ⚠ users: {str(e)[:80]}")
        
        print("\n" + "-" * 60)
        print("PRESERVED")
        print("-" * 60)
        print(f"✓ Admin: {admin_user.email if admin_user else 'N/A'}")
        print(f"✓ Roles: {db.query(Role).count()}")
        print(f"✓ Rooms: {db.query(Room).count()}")
        
        print("\n" + "=" * 60)
        print("✅ DATABASE CLEANUP COMPLETED")
        print("=" * 60)
        print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print(f"Login: {admin_user.email if admin_user else 'admin@orchid.com'}")
        print("🔄 Refresh your browser")
        print()
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("\n⚠️  WARNING: This will delete all transactional data!")
    print("Preserved: Admin, Roles, Rooms, Settings\n")
    
    response = input("Continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        clear_database_keep_admin()
    else:
        print("Cancelled.")
