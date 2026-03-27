from app.database import engine, Base
from app.models.settings import SystemSetting

print("Creating system_settings table...")
Base.metadata.create_all(bind=engine)
print("Done.")
