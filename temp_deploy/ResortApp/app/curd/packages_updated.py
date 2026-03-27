from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from typing import List

from app.models.Package import Package, PackageImage, PackageBooking, PackageBookingRoom
from app.models.room import Room
from app.schemas.packages import PackageBookingCreate


# ------------------- Packages -------------------

def create_package(db: Session, title: str, description: str, price: float, image_urls: List[str], booking_type: str = "room_type", room_types: str = None, theme: str = None, default_adults: int = 2, default_children: int = 0, max_stay_days: int = None, food_included: str = None):
    try:
        pkg = Package(
            title=title, 
            description=description, 
            price=price,
            booking_type=booking_type,
            room_types=room_types,
            theme=theme,
            default_adults=default_adults,
            default_children=default_children,
            max_stay_days=max_stay_days,
            food_included=food_included
        )
        db.add(pkg)
        db.commit()
        db.refresh(pkg)

        for url in image_urls:
            img = PackageImage(package_id=pkg.id, image_url=url)
            db.add(img)
        db.commit()
        db.refresh(pkg)
        return pkg
    except Exception as e:
        db.rollback()
        import traceback
        error_detail = f"Database error in create_package: {str(e)}\n{traceback.format_exc()}"
        print(f"ERROR: {error_detail}")
        import sys
        sys.stderr.write(f"ERROR in create_package: {error_detail}\n")
        raise HTTPException(status_code=500, detail=f"Failed to create package: {str(e)}")
