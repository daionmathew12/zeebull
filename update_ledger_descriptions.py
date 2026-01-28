from app.database import SessionLocal
from app.models.account import AccountLedger

db = SessionLocal()

updates = {
    "Room Revenue": "Revenue from room bookings",
    "Food & Beverage Revenue": "Revenue from restaurant and food orders",
    "Service Revenue": "Revenue from other services (Spa, Laundry, etc.)",
    "Other Income": "Miscellaneous income",
    "Purchases - Food": "Cost of food ingredients and raw materials",
    "Purchases - Beverages": "Cost of beverages and drinks",
    "Purchases - Inventory": "Cost of general inventory items",
    "Salaries & Wages": "Employee salaries and wages",
    "Utilities (Electricity/Water)": "Expenses for electricity, water, and gas",
    "Maintenance Expenses": "Repairs and maintenance costs for property",
    "Cost of Goods Sold": "Direct costs attributable to goods sold",
    "Cash in Hand": "Physical cash available in register",
    "Bank Account (Main)": "Primary business bank account",
    "Accounts Receivable": "Money owed by customers (Credit)",
    "Buildings": "Value of building assets",
    "Furniture & Fixtures": "Value of furniture and fixtures",
    "Computers & Equipment": "Value of computers and electronic equipment",
    "Land": "Value of land assets",
    "Share Capital": "Capital invested by shareholders",
    "Retained Earnings": "Net income retained by the business",
    "Accounts Payable": "Money owed to vendors/suppliers",
    "GST Payable": "Goods and Services Tax collected and payable",
    "Output CGST 2.5%": "Central GST collected @ 2.5%",
    "Output SGST 2.5%": "State GST collected @ 2.5%",
    "Output CGST 6%": "Central GST collected @ 6%",
    "Output SGST 6%": "State GST collected @ 6%",
    "Output CGST 9%": "Central GST collected @ 9%",
    "Output SGST 9%": "State GST collected @ 9%",
    "Input CGST 2.5%": "Central GST paid @ 2.5% (Input Credit)",
    "Input SGST 2.5%": "State GST paid @ 2.5% (Input Credit)",
    "Input CGST 6%": "Central GST paid @ 6% (Input Credit)",
    "Input SGST 6%": "State GST paid @ 6% (Input Credit)",
    "Input CGST 9%": "Central GST paid @ 9% (Input Credit)",
    "Input SGST 9%": "State GST paid @ 9% (Input Credit)",
}

count = 0
for name, description in updates.items():
    ledger = db.query(AccountLedger).filter(AccountLedger.name == name).first()
    if ledger:
        ledger.description = description
        count += 1
        print(f"Updated: {name}")

db.commit()
print(f"\nSuccessfully updated {count} ledger descriptions.")
