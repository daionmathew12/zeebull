import os
import sys

# Add ResortApp to path
current_dir = os.path.dirname(os.path.abspath(__file__))
resort_app_path = os.path.join(current_dir, "ResortApp")
if resort_app_path not in sys.path:
    sys.path.append(resort_app_path)

from app.database import SessionLocal
from app.models.branch import Branch
from app.models.room import Room
from app.models.Package import Package
from app.models.frontend import HeaderBanner, SignatureExperience, PlanWedding, NearbyAttraction
from sqlalchemy.orm import Session

def seed_data():
    db = SessionLocal()
    try:
        # 1. Ensure a branch exists
        branch = db.query(Branch).filter(Branch.id == 1).first()
        if not branch:
            print("Creating default branch...")
            branch = Branch(
                id=1,
                name="Main Branch",
                code="MAIN",
                address="123 Resort St",
                is_active=True
            )
            db.add(branch)
            db.commit()
            db.refresh(branch)
        
        # 2. Seed 10 Rooms
        print("Seeding 10 rooms...")
        for i in range(1, 11):
            room_number = f"10{i}"
            # Check if room already exists
            existing_room = db.query(Room).filter(Room.number == room_number, Room.branch_id == branch.id).first()
            if not existing_room:
                room = Room(
                    number=room_number,
                    type="Deluxe" if i % 2 == 0 else "Standard",
                    price=2500.0 + (i * 100),
                    status="Available",
                    branch_id=branch.id,
                    wifi=True,
                    air_conditioning=True
                )
                db.add(room)
        
        # 3. Seed 10 Packages
        print("Seeding 10 packages...")
        for i in range(1, 11):
            package_title = f"Test Package {i}"
            existing_package = db.query(Package).filter(Package.title == package_title, Package.branch_id == branch.id).first()
            if not existing_package:
                package = Package(
                    title=package_title,
                    description=f"This is a description for Test Package {i}",
                    price=5000.0 + (i * 500),
                    booking_type="room_type",
                    status="active",
                    branch_id=branch.id,
                    theme="General"
                )
                db.add(package)
        
        # 4. Seed 10 Banners
        print("Seeding 10 banners...")
        for i in range(1, 11):
            banner_title = f"Welcome Banner {i}"
            existing_banner = db.query(HeaderBanner).filter(HeaderBanner.title == banner_title, HeaderBanner.branch_id == branch.id).first()
            if not existing_banner:
                banner = HeaderBanner(
                    title=banner_title,
                    subtitle=f"Subtitle for banner {i}",
                    image_url=f"https://picsum.photos/1200/400?random={i}",
                    is_active=True,
                    branch_id=branch.id
                )
                db.add(banner)
        
        # 5. Seed 10 Signature Experiences
        print("Seeding 10 signature experiences...")
        for i in range(1, 11):
            experience_title = f"Experience {i}"
            existing_experience = db.query(SignatureExperience).filter(SignatureExperience.title == experience_title, SignatureExperience.branch_id == branch.id).first()
            if not existing_experience:
                experience = SignatureExperience(
                    title=experience_title,
                    description=f"Description for signature experience {i}",
                    image_url=f"https://picsum.photos/800/600?random={10+i}",
                    is_active=True,
                    branch_id=branch.id
                )
                db.add(experience)
        
        # 6. Seed 10 Plan Wedding entries
        print("Seeding 10 wedding plans...")
        for i in range(1, 11):
            wedding_title = f"Wedding Package {i}"
            existing_wedding = db.query(PlanWedding).filter(PlanWedding.title == wedding_title, PlanWedding.branch_id == branch.id).first()
            if not existing_wedding:
                wedding = PlanWedding(
                    title=wedding_title,
                    description=f"Comprehensive wedding services for package {i}",
                    image_url=f"https://picsum.photos/800/600?random={20+i}",
                    is_active=True,
                    branch_id=branch.id
                )
                db.add(wedding)
        
        # 7. Seed 10 Nearby Attractions
        print("Seeding 10 nearby attractions...")
        for i in range(1, 11):
            attraction_title = f"Attraction {i}"
            existing_attraction = db.query(NearbyAttraction).filter(NearbyAttraction.title == attraction_title, NearbyAttraction.branch_id == branch.id).first()
            if not existing_attraction:
                attraction = NearbyAttraction(
                    title=attraction_title,
                    description=f"Visit attraction {i} located near the resort.",
                    image_url=f"https://picsum.photos/800/600?random={30+i}",
                    is_active=True,
                    branch_id=branch.id
                )
                db.add(attraction)
        
        db.commit()
        print("Seeding completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
