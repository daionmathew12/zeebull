"""
Accounting Models for Resort Management System
Chart of Accounts, Ledgers, and Journal Entries
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.database import Base
import enum


class AccountType(str, enum.Enum):
    """Account Type Classification"""
    REVENUE = "Revenue"
    EXPENSE = "Expense"
    ASSET = "Asset"
    LIABILITY = "Liability"
    TAX = "Tax"


class AccountGroup(Base):
    """Account Groups - Top level categorization"""
    __tablename__ = "account_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)  # e.g., "Revenue Accounts", "Expense Accounts"
    account_type = Column(SQLEnum(AccountType), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True, server_default="1")
    
    branch = relationship("Branch")

    
    # Relationships
    ledgers = relationship("AccountLedger", back_populates="group", cascade="all, delete-orphan")


class AccountLedger(Base):
    """Individual Ledger Accounts - The actual accounts used in transactions"""
    __tablename__ = "account_ledgers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # e.g., "Room Revenue (Taxable)", "Cash in Hand"
    code = Column(String, nullable=True, unique=True)  # Optional account code for reference
    group_id = Column(Integer, ForeignKey("account_groups.id"), nullable=False)
    module = Column(String, nullable=True)  # e.g., "Booking", "Services", "Purchase"
    description = Column(Text, nullable=True)
    
    # Account properties
    opening_balance = Column(Float, default=0.0)  # Opening balance
    balance_type = Column(String, nullable=False, default="debit")  # "debit" or "credit"
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Tax specific (for GST ledgers)
    tax_type = Column(String, nullable=True)  # "CGST", "SGST", "IGST", "Output", "Input"
    tax_rate = Column(Float, nullable=True)  # Tax rate if applicable
    
    # Banking details (for bank accounts)
    bank_name = Column(String, nullable=True)
    account_number = Column(String, nullable=True)
    ifsc_code = Column(String, nullable=True)
    branch_name = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True, server_default="1")
    
    branch = relationship("Branch")

    
    # Relationships
    group = relationship("AccountGroup", back_populates="ledgers")
    debit_entries = relationship("JournalEntryLine", foreign_keys="JournalEntryLine.debit_ledger_id", back_populates="debit_ledger")
    credit_entries = relationship("JournalEntryLine", foreign_keys="JournalEntryLine.credit_ledger_id", back_populates="credit_ledger")


class JournalEntry(Base):
    """Journal Entry - Double-entry accounting transaction"""
    __tablename__ = "journal_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    entry_number = Column(String, nullable=False, unique=True)  # Auto-generated entry number
    entry_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    reference_type = Column(String, nullable=True)  # "booking", "purchase", "checkout", "consumption", "manual"
    reference_id = Column(Integer, nullable=True)  # ID of the related record (booking_id, purchase_id, etc.)
    description = Column(Text, nullable=False)
    total_amount = Column(Float, nullable=False)  # Total transaction amount
    
    # Additional metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    is_reversed = Column(Boolean, default=False)  # For reversing entries
    reversed_entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True, server_default="1")
    
    branch = relationship("Branch")

    
    # Relationships
    lines = relationship("JournalEntryLine", back_populates="entry", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])


class JournalEntryLine(Base):
    """Journal Entry Line - Individual debit/credit line in a journal entry"""
    __tablename__ = "journal_entry_lines"
    
    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("journal_entries.id"), nullable=False)
    debit_ledger_id = Column(Integer, ForeignKey("account_ledgers.id"), nullable=True)
    credit_ledger_id = Column(Integer, ForeignKey("account_ledgers.id"), nullable=True)
    amount = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    
    # Line number for ordering
    line_number = Column(Integer, nullable=False, default=1)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True, server_default="1")
    
    branch = relationship("Branch")

    
    # Relationships
    entry = relationship("JournalEntry", back_populates="lines")
    debit_ledger = relationship("AccountLedger", foreign_keys=[debit_ledger_id], back_populates="debit_entries")
    credit_ledger = relationship("AccountLedger", foreign_keys=[credit_ledger_id], back_populates="credit_entries")


