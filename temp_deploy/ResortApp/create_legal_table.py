from app.database import engine
from app.models.legal import LegalDocument

def create_tables():
    LegalDocument.metadata.create_all(bind=engine)
    print("LegalDocument table created successfully.")

if __name__ == "__main__":
    create_tables()
