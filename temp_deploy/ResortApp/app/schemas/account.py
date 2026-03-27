"""
Pydantic Schemas for Accounting Module
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class AccountType(str, Enum):
    REVENUE = "Revenue"
    EXPENSE = "Expense"
    ASSET = "Asset"
    LIABILITY = "Liability"
    TAX = "Tax"


# Account Group Schemas
class AccountGroupBase(BaseModel):
    name: str
    account_type: AccountType
    description: Optional[str] = None
    is_active: bool = True


class AccountGroupCreate(AccountGroupBase):
    pass


class AccountGroupUpdate(BaseModel):
    name: Optional[str] = None
    account_type: Optional[AccountType] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class AccountGroupOut(AccountGroupBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Account Ledger Schemas
class AccountLedgerBase(BaseModel):
    name: str
    code: Optional[str] = None
    group_id: int
    module: Optional[str] = None
    description: Optional[str] = None
    opening_balance: float = 0.0
    balance_type: str = "debit"  # "debit" or "credit"
    is_active: bool = True
    tax_type: Optional[str] = None
    tax_rate: Optional[float] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    branch_name: Optional[str] = None


class AccountLedgerCreate(AccountLedgerBase):
    pass


class AccountLedgerUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    group_id: Optional[int] = None
    module: Optional[str] = None
    description: Optional[str] = None
    opening_balance: Optional[float] = None
    balance_type: Optional[str] = None
    is_active: Optional[bool] = None
    tax_type: Optional[str] = None
    tax_rate: Optional[float] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    branch_name: Optional[str] = None


class AccountLedgerOut(AccountLedgerBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    group: Optional[AccountGroupOut] = None
    current_balance: float = 0.0
    
    class Config:
        from_attributes = True


# Journal Entry Line Schema
class JournalEntryLineBase(BaseModel):
    debit_ledger_id: Optional[int] = None
    credit_ledger_id: Optional[int] = None
    amount: float
    description: Optional[str] = None
    line_number: int = 1


class JournalEntryLineCreate(JournalEntryLineBase):
    pass


class JournalEntryLineOut(JournalEntryLineBase):
    id: int
    entry_id: int
    debit_ledger: Optional[AccountLedgerOut] = None
    credit_ledger: Optional[AccountLedgerOut] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Journal Entry Schemas
class JournalEntryBase(BaseModel):
    entry_date: datetime = Field(default_factory=datetime.utcnow)
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    description: str
    notes: Optional[str] = None


class JournalEntryLineCreateInEntry(BaseModel):
    debit_ledger_id: Optional[int] = None
    credit_ledger_id: Optional[int] = None
    amount: float
    description: Optional[str] = None


class JournalEntryCreate(JournalEntryBase):
    lines: List[JournalEntryLineCreateInEntry]


class JournalEntryUpdate(BaseModel):
    entry_date: Optional[datetime] = None
    description: Optional[str] = None
    notes: Optional[str] = None


class JournalEntryOut(JournalEntryBase):
    id: int
    entry_number: str
    total_amount: float
    created_by: Optional[int] = None
    is_reversed: bool = False
    reversed_entry_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    lines: List[JournalEntryLineOut] = []
    
    class Config:
        from_attributes = True


# Ledger Balance Schema
class LedgerBalance(BaseModel):
    ledger_id: Optional[int] = None  # None for virtual ledgers (automatic calculations)
    ledger_name: str
    debit_total: float = 0.0
    credit_total: float = 0.0
    opening_balance: float = 0.0
    balance: float = 0.0  # Positive for debit balance, negative for credit balance
    balance_type: str  # "debit" or "credit"


# Trial Balance Schema
class TrialBalance(BaseModel):
    ledgers: List[LedgerBalance]
    total_debits: float
    total_credits: float
    is_balanced: bool


