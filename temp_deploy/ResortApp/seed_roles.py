
from app.database import SessionLocal
from app.models.user import Role

db = SessionLocal()

# Define the roles we need
required_roles = [
    {"name": "housekeeping", "permissions": "[\"/housekeeping\"]"},
    {"name": "kitchen", "permissions": "[\"/kitchen\"]"},
    {"name": "waiter", "permissions": "[\"/waiter\"]"},
    {"name": "maintenance", "permissions": "[\"/maintenance\"]"},
]

print("=== SEEDING MISSING ROLES ===")
try:
    for role_data in required_roles:
        existing = db.query(Role).filter(Role.name == role_data["name"]).first()
        if existing:
            print(f"✓ Role '{role_data['name']}' already exists.")
        else:
            new_role = Role(
                name=role_data["name"],
                permissions=role_data["permissions"]
            )
            db.add(new_role)
            print(f"+ Creating role: {role_data['name']}")
    
    db.commit()
    print("\n✓ Database updated successfully.")
except Exception as e:
    db.rollback()
    print(f"Error: {e}")
finally:
    db.close()
