from app.database import engine
from sqlalchemy import text

def add_columns():
    cols = [
        ("late_checkout_fee", "FLOAT DEFAULT 0.0"),
        ("consumables_charges", "FLOAT DEFAULT 0.0"),
        ("inventory_charges", "FLOAT DEFAULT 0.0"),
        ("asset_damage_charges", "FLOAT DEFAULT 0.0"),
        ("key_card_fee", "FLOAT DEFAULT 0.0"),
        ("advance_deposit", "FLOAT DEFAULT 0.0"),
        ("tips_gratuity", "FLOAT DEFAULT 0.0"),
        ("bill_details", "JSON"),
        ("guest_gstin", "VARCHAR"),
        ("is_b2b", "BOOLEAN DEFAULT FALSE"),
        ("invoice_number", "VARCHAR"),
        ("invoice_pdf_path", "VARCHAR"),
        ("gate_pass_path", "VARCHAR"),
        ("feedback_sent", "BOOLEAN DEFAULT FALSE")
    ]
    
    with engine.connect() as conn:
        for col_name, col_type in cols:
            try:
                conn.execute(text(f"ALTER TABLE checkouts ADD COLUMN {col_name} {col_type}"))
                conn.commit()
                print(f"Added {col_name}")
            except Exception as e:
                print(f"Error adding {col_name} (might already exist): {e}")

if __name__ == "__main__":
    add_columns()
