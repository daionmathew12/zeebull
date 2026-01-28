from app.database import SessionLocal
from app.models.account import AccountLedger

db = SessionLocal()
ledgers = db.query(AccountLedger).limit(20).all()
print(f"{'ID':<5} {'Name':<30} {'Description'}")
print("-" * 60)
for l in ledgers:
    print(f"{l.id:<5} {l.name:<30} {l.description}")
