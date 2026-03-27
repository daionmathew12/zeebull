"""
Helper functions for automatic accounting entries
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from app.models.account import AccountLedger
from app.curd.account import create_journal_entry
from app.schemas.account import JournalEntryCreate, JournalEntryLineCreateInEntry


def find_ledger_by_name(db: Session, name: str, branch_id: int, module: Optional[str] = None) -> Optional[AccountLedger]:
    """Find ledger by name and branch (including global ledgers), optionally filtered by module"""
    from sqlalchemy import or_
    query = db.query(AccountLedger).filter(
        AccountLedger.name == name,
        or_(AccountLedger.branch_id == branch_id, AccountLedger.branch_id == None),
        AccountLedger.is_active == True
    )
    if module:
        query = query.filter(AccountLedger.module == module)
    return query.first()



def create_booking_journal_entry(
    db: Session,
    booking_id: int,
    room_amount: float,
    gst_amount: float,
    gst_rate: float,  # 12 or 18
    guest_name: str,
    branch_id: int,
    created_by: Optional[int] = None
) -> int:

    """
    Create journal entry for booking checkout
    Debit: Guest Receivable
    Credit: Room Revenue, Output CGST, Output SGST
    """
    # Find ledgers
    guest_receivable = find_ledger_by_name(db, "Accounts Receivable (Guest)", branch_id=branch_id, module="Booking")
    room_revenue = find_ledger_by_name(db, "Room Revenue (Taxable)", branch_id=branch_id, module="Booking")
    output_cgst = find_ledger_by_name(db, "Output CGST", branch_id=branch_id, module="Tax")
    output_sgst = find_ledger_by_name(db, "Output SGST", branch_id=branch_id, module="Tax")

    
    if not all([guest_receivable, room_revenue, output_cgst, output_sgst]):
        raise ValueError("Required ledgers not found. Please set up Chart of Accounts.")
    
    # Calculate GST split (CGST and SGST are half of total GST for intra-state)
    cgst_amount = gst_amount / 2
    sgst_amount = gst_amount / 2
    total_amount = room_amount + gst_amount
    
    # Create journal entry lines
    lines = [
        JournalEntryLineCreateInEntry(
            debit_ledger_id=guest_receivable.id,
            credit_ledger_id=None,
            amount=total_amount,
            description=f"Booking #{booking_id} - {guest_name}"
        ),
        JournalEntryLineCreateInEntry(
            debit_ledger_id=None,
            credit_ledger_id=room_revenue.id,
            amount=room_amount,
            description=f"Room revenue for booking #{booking_id}"
        ),
        JournalEntryLineCreateInEntry(
            debit_ledger_id=None,
            credit_ledger_id=output_cgst.id,
            amount=cgst_amount,
            description=f"CGST @ {gst_rate}% for booking #{booking_id}"
        ),
        JournalEntryLineCreateInEntry(
            debit_ledger_id=None,
            credit_ledger_id=output_sgst.id,
            amount=sgst_amount,
            description=f"SGST @ {gst_rate}% for booking #{booking_id}"
        )
    ]
    
    # Validate balance before creating entry
    total_debits = sum(line.amount for line in lines if line.debit_ledger_id)
    total_credits = sum(line.amount for line in lines if line.credit_ledger_id)
    
    if abs(total_debits - total_credits) > 0.01:
        error_msg = (
            f"Booking journal entry for booking {booking_id} is not balanced. "
            f"Debits: Rs.{total_debits:.2f}, Credits: Rs.{total_credits:.2f}, "
            f"Difference: Rs.{abs(total_debits - total_credits):.2f}"
        )
        print(f"[ERROR] {error_msg}")
        raise ValueError(error_msg)
    
    entry = JournalEntryCreate(
        entry_date=datetime.utcnow(),
        reference_type="booking",
        reference_id=booking_id,
        description=f"Room booking checkout - Booking #{booking_id} ({guest_name})",
        notes=f"Room amount: Rs.{room_amount}, GST: Rs.{gst_amount} @ {gst_rate}%",
        lines=lines
    )
    
    try:
        journal_entry = create_journal_entry(db, entry, branch_id=branch_id, created_by=created_by)

        print(f"[INFO] Booking journal entry {journal_entry.entry_number} created successfully (Balanced: Debits=Rs.{total_debits:.2f}, Credits=Rs.{total_credits:.2f})")
        return journal_entry.id
    except ValueError as ve:
        print(f"[ERROR] Balance validation failed for booking {booking_id}: {str(ve)}")
        raise
    except Exception as e:
        print(f"[ERROR] Error creating booking journal entry: {str(e)}")
        raise


def create_purchase_journal_entry(
    db: Session,
    purchase_id: int,
    vendor_id: int,
    inventory_amount: float,
    cgst_amount: float = 0.0,
    sgst_amount: float = 0.0,
    igst_amount: float = 0.0,
    vendor_name: str = "Unknown",
    is_interstate: bool = False,
    branch_id: int = 1,
    created_by: Optional[int] = None
) -> int:

    """
    Create journal entry for inventory purchase
    Scenario 1: Purchase of Inventory (Stock In)
    
    Example: Store Manager receives 100kg Rice from "Fresh Farms" (Invoice Rs.5,000 + 5% GST)
    - Debit: Inventory Asset Rs.5,000
    - Debit: Input SGST Rs.125
    - Debit: Input CGST Rs.125
    - Credit: Accounts Payable (Fresh Farms) Rs.5,250
    
    For inter-state purchases:
    - Debit: Inventory Asset
    - Debit: Input IGST (instead of CGST/SGST)
    - Credit: Accounts Payable
    """
    # Find ledgers
    inventory_asset = find_ledger_by_name(db, "Inventory Asset (Stock)", branch_id=branch_id, module="Inventory")
    vendor_payable = find_ledger_by_name(db, "Accounts Payable (Vendor)", branch_id=branch_id, module="Purchase")
    input_cgst = find_ledger_by_name(db, "Input CGST", branch_id=branch_id, module="Tax")
    input_sgst = find_ledger_by_name(db, "Input SGST", branch_id=branch_id, module="Tax")
    input_igst = find_ledger_by_name(db, "Input IGST", branch_id=branch_id, module="Tax")

    
    if not all([inventory_asset, vendor_payable]):
        raise ValueError("Required ledgers not found. Please set up Chart of Accounts.")
    
    # Calculate total amount
    total_amount = inventory_amount + cgst_amount + sgst_amount + igst_amount
    
    # Create journal entry lines
    lines = [
        JournalEntryLineCreateInEntry(
            debit_ledger_id=inventory_asset.id,
            credit_ledger_id=None,
            amount=inventory_amount,
            description=f"Purchase #{purchase_id} - Inventory stock"
        )
    ]
    
    # Add tax entries based on inter-state or intra-state
    if is_interstate and igst_amount > 0 and input_igst:
        lines.append(JournalEntryLineCreateInEntry(
            debit_ledger_id=input_igst.id,
            credit_ledger_id=None,
            amount=igst_amount,
            description=f"Input IGST for purchase #{purchase_id}"
        ))
    else:
        if cgst_amount > 0 and input_cgst:
            lines.append(JournalEntryLineCreateInEntry(
                debit_ledger_id=input_cgst.id,
                credit_ledger_id=None,
                amount=cgst_amount,
                description=f"Input CGST for purchase #{purchase_id}"
            ))
        if sgst_amount > 0 and input_sgst:
            lines.append(JournalEntryLineCreateInEntry(
                debit_ledger_id=input_sgst.id,
                credit_ledger_id=None,
                amount=sgst_amount,
                description=f"Input SGST for purchase #{purchase_id}"
            ))
    
    # Credit: Accounts Payable
    lines.append(JournalEntryLineCreateInEntry(
        debit_ledger_id=None,
        credit_ledger_id=vendor_payable.id,
        amount=total_amount,
        description=f"Purchase #{purchase_id} from {vendor_name}"
    ))
    
    # Validate balance before creating entry
    total_debits = sum(line.amount for line in lines if line.debit_ledger_id)
    total_credits = sum(line.amount for line in lines if line.credit_ledger_id)
    
    if abs(total_debits - total_credits) > 0.01:
        error_msg = (
            f"Purchase journal entry for purchase {purchase_id} is not balanced. "
            f"Debits: Rs.{total_debits:.2f}, Credits: Rs.{total_credits:.2f}, "
            f"Difference: Rs.{abs(total_debits - total_credits):.2f}"
        )
        print(f"[ERROR] {error_msg}")
        raise ValueError(error_msg)
    
    entry = JournalEntryCreate(
        entry_date=datetime.utcnow(),
        reference_type="purchase",
        reference_id=purchase_id,
        description=f"Inventory purchase - Purchase #{purchase_id} from {vendor_name}",
        notes=f"Inventory amount: Rs.{inventory_amount}, CGST: Rs.{cgst_amount}, SGST: Rs.{sgst_amount}, IGST: Rs.{igst_amount}, Total: Rs.{total_amount}",
        lines=lines
    )
    
    try:
        journal_entry = create_journal_entry(db, entry, branch_id=branch_id, created_by=created_by)

        print(f"[INFO] Purchase journal entry {journal_entry.entry_number} created successfully (Balanced: Debits=Rs.{total_debits:.2f}, Credits=Rs.{total_credits:.2f})")
        return journal_entry.id
    except ValueError as ve:
        print(f"[ERROR] Balance validation failed for purchase {purchase_id}: {str(ve)}")
        raise
    except Exception as e:
        print(f"[ERROR] Error creating purchase journal entry: {str(e)}")
        raise


def create_consumption_journal_entry(
    db: Session,
    consumption_id: int,
    cogs_amount: float,
    inventory_item_name: str,
    branch_id: int,
    created_by: Optional[int] = None,
    reference_type: str = "consumption"
) -> int:

    """
    Create journal entry for inventory consumption (COGS)
    Debit: Cost of Goods Sold
    Credit: Inventory Asset
    """
    # Find ledgers
    cogs = find_ledger_by_name(db, "Cost of Goods Sold (COGS)", branch_id=branch_id, module="Purchase")
    inventory_asset = find_ledger_by_name(db, "Inventory Asset (Stock)", branch_id=branch_id, module="Inventory")

    
    if not all([cogs, inventory_asset]):
        raise ValueError("Required ledgers not found. Please set up Chart of Accounts.")
    
    # Create journal entry lines
    lines = [
        JournalEntryLineCreateInEntry(
            debit_ledger_id=cogs.id,
            credit_ledger_id=None,
            amount=cogs_amount,
            description=f"Consumption #{consumption_id} - {inventory_item_name}"
        ),
        JournalEntryLineCreateInEntry(
            debit_ledger_id=None,
            credit_ledger_id=inventory_asset.id,
            amount=cogs_amount,
            description=f"Inventory consumed for consumption #{consumption_id}"
        )
    ]
    
    # Validate balance before creating entry
    total_debits = sum(line.amount for line in lines if line.debit_ledger_id)
    total_credits = sum(line.amount for line in lines if line.credit_ledger_id)
    
    if abs(total_debits - total_credits) > 0.01:
        error_msg = (
            f"Consumption journal entry for consumption {consumption_id} is not balanced. "
            f"Debits: Rs.{total_debits:.2f}, Credits: Rs.{total_credits:.2f}, "
            f"Difference: Rs.{abs(total_debits - total_credits):.2f}"
        )
        print(f"[ERROR] {error_msg}")
        raise ValueError(error_msg)
    
    entry = JournalEntryCreate(
        entry_date=datetime.utcnow(),
        reference_type=reference_type,
        reference_id=consumption_id,
        description=f"Inventory consumption - {inventory_item_name}",
        notes=f"COGS: Rs.{cogs_amount}",
        lines=lines
    )
    
    try:
        journal_entry = create_journal_entry(db, entry, branch_id=branch_id, created_by=created_by)

        print(f"[INFO] Consumption journal entry {journal_entry.entry_number} created successfully (Balanced: Debits=Rs.{total_debits:.2f}, Credits=Rs.{total_credits:.2f})")
        return journal_entry.id
    except ValueError as ve:
        print(f"[ERROR] Balance validation failed for consumption {consumption_id}: {str(ve)}")
        raise
    except Exception as e:
        print(f"[ERROR] Error creating consumption journal entry: {str(e)}")
        raise


def create_complimentary_journal_entry(
    db: Session,
    complimentary_id: int,
    expense_amount: float,
    item_name: str,
    room_number: str,
    branch_id: int,
    created_by: Optional[int] = None
) -> int:

    """
    Create journal entry for complimentary items
    Debit: Consumables Expense
    Credit: Inventory Asset
    """
    # Find ledgers
    consumables_expense = find_ledger_by_name(db, "Consumables Expense", branch_id=branch_id, module="Purchase")
    inventory_asset = find_ledger_by_name(db, "Inventory Asset (Stock)", branch_id=branch_id, module="Inventory")

    
    if not all([consumables_expense, inventory_asset]):
        raise ValueError("Required ledgers not found. Please set up Chart of Accounts.")
    
    # Create journal entry lines
    lines = [
        JournalEntryLineCreateInEntry(
            debit_ledger_id=consumables_expense.id,
            credit_ledger_id=None,
            amount=expense_amount,
            description=f"Complimentary #{complimentary_id} - {item_name} (Room {room_number})"
        ),
        JournalEntryLineCreateInEntry(
            debit_ledger_id=None,
            credit_ledger_id=inventory_asset.id,
            amount=expense_amount,
            description=f"Complimentary item consumed - {item_name}"
        )
    ]
    
    # Validate balance before creating entry
    total_debits = sum(line.amount for line in lines if line.debit_ledger_id)
    total_credits = sum(line.amount for line in lines if line.credit_ledger_id)
    
    if abs(total_debits - total_credits) > 0.01:
        error_msg = (
            f"Complimentary journal entry for complimentary {complimentary_id} is not balanced. "
            f"Debits: Rs.{total_debits:.2f}, Credits: Rs.{total_credits:.2f}, "
            f"Difference: Rs.{abs(total_debits - total_credits):.2f}"
        )
        print(f"[ERROR] {error_msg}")
        raise ValueError(error_msg)
    
    entry = JournalEntryCreate(
        entry_date=datetime.utcnow(),
        reference_type="complimentary",
        reference_id=complimentary_id,
        description=f"Complimentary item - {item_name} (Room {room_number})",
        notes=f"Expense: Rs.{expense_amount}",
        lines=lines
    )
    
    try:
        journal_entry = create_journal_entry(db, entry, branch_id=branch_id, created_by=created_by)

        print(f"[INFO] Complimentary journal entry {journal_entry.entry_number} created successfully (Balanced: Debits=Rs.{total_debits:.2f}, Credits=Rs.{total_credits:.2f})")
        return journal_entry.id
    except ValueError as ve:
        print(f"[ERROR] Balance validation failed for complimentary {complimentary_id}: {str(ve)}")
        raise
    except Exception as e:
        print(f"[ERROR] Error creating complimentary journal entry: {str(e)}")
        raise


def create_food_order_journal_entry(
    db: Session,
    food_order_id: int,
    amount: float,
    room_number: str,
    branch_id: int,
    gst_rate: float = 5.0,  # Default 5% GST for food

    created_by: Optional[int] = None
) -> int:
    """
    Create journal entry for food order revenue
    Debit: Guest Receivable
    Credit: Food Revenue, Output CGST, Output SGST
    """
    # Find ledgers
    guest_receivable = find_ledger_by_name(db, "Accounts Receivable (Guest)", branch_id=branch_id, module="Booking")
    food_revenue = find_ledger_by_name(db, "Food Revenue (Taxable)", branch_id=branch_id, module="Food")
    output_cgst = find_ledger_by_name(db, "Output CGST", branch_id=branch_id, module="Tax")
    output_sgst = find_ledger_by_name(db, "Output SGST", branch_id=branch_id, module="Tax")

    
    if not all([guest_receivable, food_revenue, output_cgst, output_sgst]):
        raise ValueError("Required ledgers not found. Please set up Chart of Accounts.")
    
    # Calculate GST (Back-calculate from Total Amount - Inclusive)
    # Total = Base * (1 + Rate/100)
    # Base = Total / (1 + Rate/100)
    base_amount = amount / (1 + (gst_rate / 100))
    gst_amount = amount - base_amount
    cgst_amount = gst_amount / 2
    sgst_amount = gst_amount / 2
    
    # Create journal entry lines
    lines = [
        JournalEntryLineCreateInEntry(
            debit_ledger_id=guest_receivable.id,
            credit_ledger_id=None,
            amount=amount,
            description=f"Food Order #{food_order_id} - Room {room_number}"
        ),
        JournalEntryLineCreateInEntry(
            debit_ledger_id=None,
            credit_ledger_id=food_revenue.id,
            amount=base_amount,
            description=f"Food revenue for order #{food_order_id}"
        ),
        JournalEntryLineCreateInEntry(
            debit_ledger_id=None,
            credit_ledger_id=output_cgst.id,
            amount=cgst_amount,
            description=f"CGST @ {gst_rate}% for food order #{food_order_id}"
        ),
        JournalEntryLineCreateInEntry(
            debit_ledger_id=None,
            credit_ledger_id=output_sgst.id,
            amount=sgst_amount,
            description=f"SGST @ {gst_rate}% for food order #{food_order_id}"
        )
    ]
    
    # Validate balance before creating entry
    total_debits = sum(line.amount for line in lines if line.debit_ledger_id)
    total_credits = sum(line.amount for line in lines if line.credit_ledger_id)
    
    if abs(total_debits - total_credits) > 0.01:
        error_msg = (
            f"Food order journal entry for order {food_order_id} is not balanced. "
            f"Debits: Rs.{total_debits:.2f}, Credits: Rs.{total_credits:.2f}, "
            f"Difference: Rs.{abs(total_debits - total_credits):.2f}"
        )
        print(f"[ERROR] {error_msg}")
        raise ValueError(error_msg)
    
    entry = JournalEntryCreate(
        entry_date=datetime.utcnow(),
        reference_type="food_order",
        reference_id=food_order_id,
        description=f"Food order revenue - Order #{food_order_id} (Room {room_number})",
        notes=f"Food amount: Rs.{base_amount}, GST: Rs.{gst_amount} @ {gst_rate}%",
        lines=lines
    )
    
    try:
        journal_entry = create_journal_entry(db, entry, branch_id=branch_id, created_by=created_by)

        print(f"[INFO] Food order journal entry {journal_entry.entry_number} created successfully (Balanced: Debits=Rs.{total_debits:.2f}, Credits=Rs.{total_credits:.2f})")
        return journal_entry.id
    except ValueError as ve:
        print(f"[ERROR] Balance validation failed for food order {food_order_id}: {str(ve)}")
        raise
    except Exception as e:
        print(f"[ERROR] Error creating food order journal entry: {str(e)}")
        raise


def create_service_revenue_journal_entry(
    db: Session,
    service_id: int,
    amount: float,
    room_number: str,
    service_name: str,
    branch_id: int,
    gst_rate: float = 18.0,  # Default 18% GST for services

    created_by: Optional[int] = None
) -> int:
    """
    Create journal entry for service revenue
    Debit: Guest Receivable
    Credit: Service Revenue, Output CGST, Output SGST
    """
    # Find ledgers
    guest_receivable = find_ledger_by_name(db, "Accounts Receivable (Guest)", branch_id=branch_id, module="Booking")
    service_revenue = find_ledger_by_name(db, "Service Revenue (Taxable)", branch_id=branch_id, module="Service")
    output_cgst = find_ledger_by_name(db, "Output CGST", branch_id=branch_id, module="Tax")
    output_sgst = find_ledger_by_name(db, "Output SGST", branch_id=branch_id, module="Tax")

    
    if not all([guest_receivable, service_revenue, output_cgst, output_sgst]):
        raise ValueError("Required ledgers not found. Please set up Chart of Accounts.")
    
    # Calculate GST (Back-calculate from Total Amount - Inclusive)
    # Total = Base * (1 + Rate/100)
    # Base = Total / (1 + Rate/100)
    base_amount = amount / (1 + (gst_rate / 100))
    gst_amount = amount - base_amount
    cgst_amount = gst_amount / 2
    sgst_amount = gst_amount / 2
    
    # Create journal entry lines
    lines = [
        JournalEntryLineCreateInEntry(
            debit_ledger_id=guest_receivable.id,
            credit_ledger_id=None,
            amount=amount,
            description=f"Service #{service_id} - {service_name} (Room {room_number})"
        ),
        JournalEntryLineCreateInEntry(
            debit_ledger_id=None,
            credit_ledger_id=service_revenue.id,
            amount=base_amount,
            description=f"Service revenue for service #{service_id}"
        ),
        JournalEntryLineCreateInEntry(
            debit_ledger_id=None,
            credit_ledger_id=output_cgst.id,
            amount=cgst_amount,
            description=f"CGST @ {gst_rate}% for service #{service_id}"
        ),
        JournalEntryLineCreateInEntry(
            debit_ledger_id=None,
            credit_ledger_id=output_sgst.id,
            amount=sgst_amount,
            description=f"SGST @ {gst_rate}% for service #{service_id}"
        )
    ]
    
    # Validate balance before creating entry
    total_debits = sum(line.amount for line in lines if line.debit_ledger_id)
    total_credits = sum(line.amount for line in lines if line.credit_ledger_id)
    
    if abs(total_debits - total_credits) > 0.01:
        error_msg = (
            f"Service journal entry for service {service_id} is not balanced. "
            f"Debits: Rs.{total_debits:.2f}, Credits: Rs.{total_credits:.2f}, "
            f"Difference: Rs.{abs(total_debits - total_credits):.2f}"
        )
        print(f"[ERROR] {error_msg}")
        raise ValueError(error_msg)
    
    entry = JournalEntryCreate(
        entry_date=datetime.utcnow(),
        reference_type="service",
        reference_id=service_id,
        description=f"Service revenue - {service_name} (Room {room_number})",
        notes=f"Service amount: Rs.{base_amount}, GST: Rs.{gst_amount} @ {gst_rate}%",
        lines=lines
    )
    
    try:
        journal_entry = create_journal_entry(db, entry, branch_id=branch_id, created_by=created_by)

        print(f"[INFO] Service journal entry {journal_entry.entry_number} created successfully (Balanced: Debits=Rs.{total_debits:.2f}, Credits=Rs.{total_credits:.2f})")
        return journal_entry.id
    except ValueError as ve:
        print(f"[ERROR] Balance validation failed for service {service_id}: {str(ve)}")
        raise
    except Exception as e:
        print(f"[ERROR] Error creating service journal entry: {str(e)}")
        raise


def create_expense_journal_entry(
    db: Session,
    expense_id: int,
    amount: float,
    category: str,
    description: str,
    branch_id: int,
    created_by: Optional[int] = None
) -> int:

    """
    Create journal entry for expense
    Debit: Expense Ledger (based on category)
    Credit: Cash/Bank
    """
    # Find ledgers - try to find expense ledger by category name
    expense_ledger = find_ledger_by_name(db, f"{category} Expense", branch_id=branch_id, module="Expense")
    if not expense_ledger:
        # Fallback to general expense ledger
        expense_ledger = find_ledger_by_name(db, "General Expense", branch_id=branch_id, module="Expense")
    
    cash_ledger = find_ledger_by_name(db, "Cash", branch_id=branch_id, module="Asset")
    if not cash_ledger:
        cash_ledger = find_ledger_by_name(db, "Bank Account", branch_id=branch_id, module="Asset")

    
    if not all([expense_ledger, cash_ledger]):
        raise ValueError("Required ledgers not found. Please set up Chart of Accounts.")
    
    # Create journal entry lines
    lines = [
        JournalEntryLineCreateInEntry(
            debit_ledger_id=expense_ledger.id,
            credit_ledger_id=None,
            amount=amount,
            description=f"Expense #{expense_id} - {category}: {description}"
        ),
        JournalEntryLineCreateInEntry(
            debit_ledger_id=None,
            credit_ledger_id=cash_ledger.id,
            amount=amount,
            description=f"Payment for expense #{expense_id}"
        )
    ]
    
    # Validate balance before creating entry
    total_debits = sum(line.amount for line in lines if line.debit_ledger_id)
    total_credits = sum(line.amount for line in lines if line.credit_ledger_id)
    
    if abs(total_debits - total_credits) > 0.01:
        error_msg = (
            f"Expense journal entry for expense {expense_id} is not balanced. "
            f"Debits: Rs.{total_debits:.2f}, Credits: Rs.{total_credits:.2f}, "
            f"Difference: Rs.{abs(total_debits - total_credits):.2f}"
        )
        print(f"[ERROR] {error_msg}")
        raise ValueError(error_msg)
    
    entry = JournalEntryCreate(
        entry_date=datetime.utcnow(),
        reference_type="expense",
        reference_id=expense_id,
        description=f"Expense - {category}: {description}",
        notes=f"Amount: Rs.{amount}",
        lines=lines
    )
    
    try:
        journal_entry = create_journal_entry(db, entry, branch_id=branch_id, created_by=created_by)

        print(f"[INFO] Expense journal entry {journal_entry.entry_number} created successfully (Balanced: Debits=Rs.{total_debits:.2f}, Credits=Rs.{total_credits:.2f})")
        return journal_entry.id
    except ValueError as ve:
        print(f"[ERROR] Balance validation failed for expense {expense_id}: {str(ve)}")
        raise
    except Exception as e:
        print(f"[ERROR] Error creating expense journal entry: {str(e)}")
        raise


def create_complete_checkout_journal_entry(
    db: Session,
    checkout_id: int,
    room_total: float,
    food_total: float,
    service_total: float,
    package_total: float,
    tax_amount: float,
    discount_amount: float,
    grand_total: float,
    guest_name: str,
    room_number: str,
    branch_id: int,
    gst_rate: float = 12.0,  # Default GST rate

    payment_method: str = "cash",  # cash, card, upi, etc.
    payment_ledger_id: Optional[int] = None,  # Optional: specify payment ledger directly
    created_by: Optional[int] = None,
    advance_amount: float = 0.0
) -> int:
    """
    Create comprehensive journal entry for complete checkout (Scenario 2: Guest Checkout)
    
    Example: Guest pays Rs.11,800 (Rs.10k Room + 18% GST) by Swipe Card
    - Debit: Bank Account (HDFC) Rs.11,800
    - Credit: Room Revenue Rs.10,000
    - Credit: Output CGST Rs.900
    - Credit: Output SGST Rs.900
    
    Includes room, food, services, and all charges
    """
    # Find ledgers
    room_revenue = find_ledger_by_name(db, "Room Revenue (Taxable)", branch_id=branch_id, module="Booking")
    food_revenue = find_ledger_by_name(db, "Food Revenue (Taxable)", branch_id=branch_id, module="Food")
    service_revenue = find_ledger_by_name(db, "Service Revenue (Taxable)", branch_id=branch_id, module="Service")
    package_revenue = find_ledger_by_name(db, "Package Revenue (Taxable)", branch_id=branch_id, module="Booking")
    output_cgst = find_ledger_by_name(db, "Output CGST", branch_id=branch_id, module="Tax")
    output_sgst = find_ledger_by_name(db, "Output SGST", branch_id=branch_id, module="Tax")
    output_igst = find_ledger_by_name(db, "Output IGST", branch_id=branch_id, module="Tax")
    discount_ledger = find_ledger_by_name(db, "Discount Allowed", branch_id=branch_id, module="Expense")
    advance_ledger = find_ledger_by_name(db, "Advance from Customers", branch_id=branch_id, module="Liability")

    
    # Relaxed validation: Only require ledgers for components that have non-zero amounts
    if room_total > 0 and not room_revenue:
        print(f"[WARNING] Cannot create journal entry for checkout {checkout_id}: Missing 'Room Revenue (Taxable)' ledger")
        return None
    
    if food_total > 0 and not food_revenue:
        print(f"[WARNING] Cannot create journal entry for checkout {checkout_id}: Missing 'Food Revenue (Taxable)' ledger")
        return None
        
    if service_total > 0 and not service_revenue:
        # Try finding generic service revenue if specific one missing
        service_revenue = find_ledger_by_name(db, "Service Revenue", branch_id=branch_id, module="Service")

        if not service_revenue:
            print(f"[WARNING] Cannot create journal entry for checkout {checkout_id}: Missing 'Service Revenue (Taxable)' ledger")
            return None

    if package_total > 0 and not package_revenue:
         # Try finding generic package revenue
        package_revenue = find_ledger_by_name(db, "Package Revenue", branch_id=branch_id, module="Booking")

        if not package_revenue:
             print(f"[WARNING] Cannot create journal entry for checkout {checkout_id}: Missing 'Package Revenue (Taxable)' ledger")
             return None

    if tax_amount > 0 and (not output_cgst or not output_sgst):
        print(f"[WARNING] Cannot create journal entry for checkout {checkout_id}: Missing Tax ledgers (Output CGST/SGST)")
        return None
    
    # Determine payment ledger (Bank Account or Cash)
    if payment_ledger_id:
        from app.models.account import AccountLedger
        payment_ledger = db.query(AccountLedger).filter(AccountLedger.id == payment_ledger_id, AccountLedger.branch_id == branch_id).first()

    else:
        payment_method_lower = payment_method.lower() if payment_method else "cash"
        if payment_method_lower in ["card", "swipe", "debit", "credit", "upi", "netbanking"]:
            # Use Bank Account (try HDFC first, then SBI, then any bank)
            payment_ledger = find_ledger_by_name(db, "Bank Account (HDFC)", branch_id=branch_id, module="Asset")
            if not payment_ledger:
                payment_ledger = find_ledger_by_name(db, "Bank Account (SBI)", branch_id=branch_id, module="Asset")
            if not payment_ledger:
                from app.models.account import AccountLedger
                payment_ledger = db.query(AccountLedger).filter(
                    AccountLedger.name.like("Bank Account%"),
                    AccountLedger.branch_id == branch_id,
                    AccountLedger.is_active == True
                ).first()
        else:
            # Cash payment
            payment_ledger = find_ledger_by_name(db, "Cash in Hand", branch_id=branch_id, module="Asset")

    
    if not payment_ledger:
        print(f"[WARNING] Cannot create journal entry for checkout {checkout_id}: Payment ledger (Bank Account or Cash) not found. Please set up Chart of Accounts.")
        return None  # Return None instead of raising error
    
    # Calculate base amounts (excluding GST from totals)
    # For simplicity, assume tax_amount is the total GST
    cgst_amount = tax_amount / 2
    sgst_amount = tax_amount / 2
    igst_amount = 0.0  # Can be enhanced for inter-state sales
    
    # Calculate total revenue before tax
    total_revenue = room_total + food_total + service_total + package_total - discount_amount
    
    # Create journal entry lines
    lines = []
    
    # Debit: Bank Account / Cash (total amount received)
    lines.append(JournalEntryLineCreateInEntry(
        debit_ledger_id=payment_ledger.id,
        credit_ledger_id=None,
        amount=grand_total,
        description=f"Checkout #{checkout_id} - {guest_name} (Room {room_number}) - Payment via {payment_method}"
    ))
    
    # Credit: Room Revenue
    if room_total > 0:
        lines.append(JournalEntryLineCreateInEntry(
            debit_ledger_id=None,
            credit_ledger_id=room_revenue.id,
            amount=room_total,
            description=f"Room revenue for checkout #{checkout_id}"
        ))
    
    # Credit: Food Revenue
    if food_total > 0:
        lines.append(JournalEntryLineCreateInEntry(
            debit_ledger_id=None,
            credit_ledger_id=food_revenue.id,
            amount=food_total,
            description=f"Food revenue for checkout #{checkout_id}"
        ))
    
    # Credit: Service Revenue
    if service_total > 0:
        lines.append(JournalEntryLineCreateInEntry(
            debit_ledger_id=None,
            credit_ledger_id=service_revenue.id,
            amount=service_total,
            description=f"Service revenue for checkout #{checkout_id}"
        ))
    
    # Credit: Package Revenue
    if package_total > 0 and package_revenue:
        lines.append(JournalEntryLineCreateInEntry(
            debit_ledger_id=None,
            credit_ledger_id=package_revenue.id,
            amount=package_total,
            description=f"Package revenue for checkout #{checkout_id}"
        ))
    
    # Credit: Output CGST
    if cgst_amount > 0:
        lines.append(JournalEntryLineCreateInEntry(
            debit_ledger_id=None,
            credit_ledger_id=output_cgst.id,
            amount=cgst_amount,
            description=f"CGST for checkout #{checkout_id}"
        ))
    
    # Credit: Output SGST
    if sgst_amount > 0:
        lines.append(JournalEntryLineCreateInEntry(
            debit_ledger_id=None,
            credit_ledger_id=output_sgst.id,
            amount=sgst_amount,
            description=f"SGST for checkout #{checkout_id}"
        ))
    
    # Debit: Discount Allowed (if discount exists)
    if discount_amount > 0 and discount_ledger:
        lines.append(JournalEntryLineCreateInEntry(
            debit_ledger_id=discount_ledger.id,
            credit_ledger_id=None,
            amount=discount_amount,
            description=f"Discount for checkout #{checkout_id}"
        ))

    # Debit: Advance from Customers (utilizing advance payment)
    if advance_amount > 0:
        if advance_ledger:
            lines.append(JournalEntryLineCreateInEntry(
                debit_ledger_id=advance_ledger.id,
                credit_ledger_id=None,
                amount=advance_amount,
                description=f"Advance adjusted for checkout #{checkout_id}"
            ))
        else:
            # Fallback if advance ledger missing: reduce debit from bank? No, creates imbalance.
            print(f"[WARNING] Advance ledger missing for checkout {checkout_id}. Journal Entry will be unbalanced!")
            # Note: We continue, but validation will strictly fail below unless we do something.
            # If we strictly enforce balance, this will raise ValueError.
            pass
    
    # Validate that we have at least one line
    if not lines:
        print(f"[WARNING] No journal entry lines to create for checkout {checkout_id}")
        return None
    
    # Validate balance before creating entry
    total_debits = sum(line.amount for line in lines if line.debit_ledger_id)
    total_credits = sum(line.amount for line in lines if line.credit_ledger_id)
    
    # Check if entry is balanced (allow small rounding differences)
    if abs(total_debits - total_credits) > 0.01:
        error_msg = (
            f"Journal entry for checkout {checkout_id} is not balanced. "
            f"Debits: Rs.{total_debits:.2f}, Credits: Rs.{total_credits:.2f}, "
            f"Difference: Rs.{abs(total_debits - total_credits):.2f}"
        )
        print(f"[ERROR] {error_msg}")
        raise ValueError(error_msg)
    
    entry = JournalEntryCreate(
        entry_date=datetime.utcnow(),
        reference_type="checkout",
        reference_id=checkout_id,
        description=f"Complete checkout - {guest_name} (Room {room_number})",
        notes=f"Room: Rs.{room_total}, Food: Rs.{food_total}, Service: Rs.{service_total}, Package: Rs.{package_total}, Tax: Rs.{tax_amount}, Discount: Rs.{discount_amount}, Total: Rs.{grand_total}",
        lines=lines
    )
    
    try:
        journal_entry = create_journal_entry(db, entry, created_by)
        print(f"[INFO] Journal entry {journal_entry.entry_number} created successfully for checkout {checkout_id} (Balanced: Debits=Rs.{total_debits:.2f}, Credits=Rs.{total_credits:.2f})")
        return journal_entry.id
    except ValueError as ve:
        # Re-raise validation errors
        print(f"[ERROR] Balance validation failed for checkout {checkout_id}: {str(ve)}")
        raise
    except Exception as e:
        print(f"[WARNING] Error creating journal entry for checkout {checkout_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def generate_rcm_self_invoice_number(db: Session) -> str:
    """
    Generate self-invoice number for RCM transactions
    Format: SLF-YYYY-XXX (e.g., SLF-2025-001)
    """
    from datetime import datetime
    current_year = datetime.now().year
    
    # Find the highest invoice number for this year
    from app.models.expense import Expense
    from sqlalchemy import func
    
    # Query for existing self-invoices this year
    max_invoice = db.query(func.max(Expense.self_invoice_number)).filter(
        Expense.self_invoice_number.like(f"SLF-{current_year}-%")
    ).scalar()
    
    if max_invoice:
        # Extract the number part and increment
        try:
            number_part = int(max_invoice.split('-')[-1])
            next_number = number_part + 1
        except (ValueError, IndexError):
            next_number = 1
    else:
        next_number = 1
    
    return f"SLF-{current_year}-{str(next_number).zfill(3)}"


def create_rcm_journal_entry(
    db: Session,
    taxable_value: float,
    tax_rate: float,
    expense_id: Optional[int] = None,
    purchase_id: Optional[int] = None,
    is_interstate: bool = False,
    nature_of_supply: str = "GTA",
    vendor_name: str = "Unknown",
    self_invoice_number: Optional[str] = None,
    itc_eligible: bool = True,
    created_by: Optional[int] = None
) -> int:
    """
    Create journal entry for RCM (Reverse Charge Mechanism) transaction
    
    Logic:
    - Debit: Expense/Purchase Ledger (taxable value)
    - Debit: Input IGST/CGST/SGST (if ITC eligible)
    - Credit: Cash/Bank (taxable value - vendor gets no tax)
    - Credit: Output IGST/CGST/SGST RCM Payable (tax liability)
    
    Example: You pay a Lawyer Rs.50,000 fees (RCM @ 18%)
    - Debit Legal Fees Rs.50,000 | Credit Bank Rs.50,000
    - Debit Input IGST (RCM) Rs.9,000 | Credit Output IGST (RCM Payable) Rs.9,000
    
    Args:
        expense_id: ID of expense record (if RCM from expense)
        purchase_id: ID of purchase record (if RCM from purchase)
        taxable_value: Base amount (vendor gets this, no tax)
        tax_rate: GST rate (e.g., 5% for GTA, 18% for Legal)
        is_interstate: True for IGST, False for CGST/SGST
        nature_of_supply: GTA, Legal Services, Import of Service, Security Services
        vendor_name: Name of vendor
        self_invoice_number: Self-invoice number (SLF-YYYY-XXX)
        itc_eligible: Can you claim ITC? (Usually Yes)
        created_by: User ID who created this
    
    Returns:
        Journal entry ID
    """
    # Calculate tax amounts
    tax_amount = taxable_value * (tax_rate / 100)
    
    if is_interstate:
        # IGST (inter-state)
        igst_amount = tax_amount
        cgst_amount = 0.0
        sgst_amount = 0.0
    else:
        # CGST + SGST (intra-state)
        igst_amount = 0.0
        cgst_amount = tax_amount / 2
        sgst_amount = tax_amount / 2
    
    # Find ledgers
    # Expense/Purchase ledger (based on category or nature)
    expense_ledger_name = f"{nature_of_supply} Expense" if expense_id else "Purchase Expense"
    expense_ledger = find_ledger_by_name(db, expense_ledger_name, "Expense")
    if not expense_ledger:
        expense_ledger = find_ledger_by_name(db, "General Expense", "Expense")
    
    # Input tax ledgers (if ITC eligible)
    input_igst = find_ledger_by_name(db, "Input IGST (RCM)", "Tax") if itc_eligible else None
    input_cgst = find_ledger_by_name(db, "Input CGST (RCM)", "Tax") if itc_eligible else None
    input_sgst = find_ledger_by_name(db, "Input SGST (RCM)", "Tax") if itc_eligible else None
    
    # Output tax ledgers (RCM Payable - liability)
    output_igst_rcm = find_ledger_by_name(db, "Output IGST (RCM Payable)", "Tax")
    output_cgst_rcm = find_ledger_by_name(db, "Output CGST (RCM Payable)", "Tax")
    output_sgst_rcm = find_ledger_by_name(db, "Output SGST (RCM Payable)", "Tax")
    
    # Cash/Bank ledger
    cash_ledger = find_ledger_by_name(db, "Cash", "Asset")
    if not cash_ledger:
        cash_ledger = find_ledger_by_name(db, "Bank Account", "Asset")
    
    if not all([expense_ledger, cash_ledger, output_igst_rcm, output_cgst_rcm, output_sgst_rcm]):
        raise ValueError("Required ledgers not found. Please set up Chart of Accounts for RCM.")
    
    # Create journal entry lines
    lines = []
    
    # 1. Debit: Expense/Purchase (taxable value)
    lines.append(JournalEntryLineCreateInEntry(
        debit_ledger_id=expense_ledger.id,
        credit_ledger_id=None,
        amount=taxable_value,
        description=f"RCM {nature_of_supply} - {vendor_name} ({self_invoice_number or 'N/A'})"
    ))
    
    # 2. Credit: Cash/Bank (taxable value - vendor gets no tax)
    lines.append(JournalEntryLineCreateInEntry(
        debit_ledger_id=None,
        credit_ledger_id=cash_ledger.id,
        amount=taxable_value,
        description=f"Payment to {vendor_name} (RCM - no tax charged)"
    ))
    
    # 3. If ITC eligible: Debit Input Tax
    if itc_eligible:
        if igst_amount > 0 and input_igst:
            lines.append(JournalEntryLineCreateInEntry(
                debit_ledger_id=input_igst.id,
                credit_ledger_id=None,
                amount=igst_amount,
                description=f"Input IGST (RCM) @ {tax_rate}% - {self_invoice_number or 'N/A'}"
            ))
        if cgst_amount > 0 and input_cgst:
            lines.append(JournalEntryLineCreateInEntry(
                debit_ledger_id=input_cgst.id,
                credit_ledger_id=None,
                amount=cgst_amount,
                description=f"Input CGST (RCM) @ {tax_rate}% - {self_invoice_number or 'N/A'}"
            ))
        if sgst_amount > 0 and input_sgst:
            lines.append(JournalEntryLineCreateInEntry(
                debit_ledger_id=input_sgst.id,
                credit_ledger_id=None,
                amount=sgst_amount,
                description=f"Input SGST (RCM) @ {tax_rate}% - {self_invoice_number or 'N/A'}"
            ))
    
    # 4. Credit: Output Tax RCM Payable (liability to pay to government)
    if igst_amount > 0:
        lines.append(JournalEntryLineCreateInEntry(
            debit_ledger_id=None,
            credit_ledger_id=output_igst_rcm.id,
            amount=igst_amount,
            description=f"Output IGST (RCM Payable) @ {tax_rate}% - {self_invoice_number or 'N/A'}"
        ))
    if cgst_amount > 0:
        lines.append(JournalEntryLineCreateInEntry(
            debit_ledger_id=None,
            credit_ledger_id=output_cgst_rcm.id,
            amount=cgst_amount,
            description=f"Output CGST (RCM Payable) @ {tax_rate}% - {self_invoice_number or 'N/A'}"
        ))
    if sgst_amount > 0:
        lines.append(JournalEntryLineCreateInEntry(
            debit_ledger_id=None,
            credit_ledger_id=output_sgst_rcm.id,
            amount=sgst_amount,
            description=f"Output SGST (RCM Payable) @ {tax_rate}% - {self_invoice_number or 'N/A'}"
        ))
    
    # Determine reference type and ID
    ref_type = "expense_rcm" if expense_id else "purchase_rcm"
    ref_id = expense_id or purchase_id
    
    # Validate balance before creating entry
    total_debits = sum(line.amount for line in lines if line.debit_ledger_id)
    total_credits = sum(line.amount for line in lines if line.credit_ledger_id)
    
    if abs(total_debits - total_credits) > 0.01:
        error_msg = (
            f"RCM journal entry for {ref_type} {ref_id} is not balanced. "
            f"Debits: Rs.{total_debits:.2f}, Credits: Rs.{total_credits:.2f}, "
            f"Difference: Rs.{abs(total_debits - total_credits):.2f}"
        )
        print(f"[ERROR] {error_msg}")
        raise ValueError(error_msg)
    
    entry = JournalEntryCreate(
        entry_date=datetime.utcnow(),
        reference_type=ref_type,
        reference_id=ref_id,
        description=f"RCM Transaction - {nature_of_supply} from {vendor_name}",
        notes=f"Self-Invoice: {self_invoice_number or 'N/A'}, Taxable Value: Rs.{taxable_value}, Tax Rate: {tax_rate}%, Tax Amount: Rs.{tax_amount}, ITC Eligible: {itc_eligible}",
        lines=lines
    )
    
    try:
        journal_entry = create_journal_entry(db, entry, created_by)
        print(f"[INFO] RCM journal entry {journal_entry.entry_number} created successfully (Balanced: Debits=Rs.{total_debits:.2f}, Credits=Rs.{total_credits:.2f})")
        return journal_entry.id
    except ValueError as ve:
        print(f"[ERROR] Balance validation failed for RCM {ref_type} {ref_id}: {str(ve)}")
        raise
    except Exception as e:
        print(f"[ERROR] Error creating RCM journal entry: {str(e)}")
        raise

