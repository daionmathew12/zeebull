from app.database import SessionLocal
from app.models.Package import PackageImage

db = SessionLocal()
try:
    img = db.query(PackageImage).filter(PackageImage.package_id == 20).first()
    if img:
        img.image_url = '/uploads/packages/pkg_52990caf7c394a8ea1284aea4a1796a8_blob'
        db.commit()
        print('Updated image for package 20 to existing file.')
    else:
        print('Package 20 image not found.')
except Exception as e:
    print(f'Error: {e}')
    db.rollback()
finally:
    db.close()
