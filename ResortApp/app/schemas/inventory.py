from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


# Category Schemas
class InventoryCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

    # Basic Identification
    parent_department: Optional[str] = None  # Restaurant, Facility, Hotel, Office, Fire & Safety, Security
    gst_tax_rate: float = 0.0  # 5%, 12%, 18%, 28% - Essential for Purchase Logic
    
    # GST Classification Properties
    classification: Optional[str] = None  # "Goods" or "Services"
    hsn_sac_code: Optional[str] = None  # 4, 6, or 8 digits - Essential for GST Compliance
    default_gst_rate: float = 0.0  # 0%, 5%, 12%, 18%, 28%
    cess_percentage: float = 0.0  # Additional cess
    
    # ITC (Input Tax Credit) Rules
    itc_eligibility: str = "Eligible"  # "Eligible" or "Ineligible (Blocked)"
    is_capital_good: bool = False
    
    # Logic Switches (The "Brain" of the System)
    is_perishable: bool = False  # Activates Logic 1.1: Expiry-based alerts
    is_asset_fixed: bool = False  # Activates Logic 2.2 & 6.2: Auto-generates maintenance reminders
    is_sellable: bool = False  # Activates Logic 3.2: If usage exceeds limit, add charge to customer billing
    track_laundry: bool = False  # Activates Logic 5.4: Enables "Fresh -> Used -> Laundry -> Fresh" cycle
    allow_partial_usage: bool = False  # Activates Logic 1.2: Kitchen raises stock usage request by weight/volume
    consumable_instant: bool = False  # Activates Logic 4.1: System deducts requested quantity immediately upon issuance


class InventoryCategoryCreate(InventoryCategoryBase):
    pass


class InventoryCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_department: Optional[str] = None
    gst_tax_rate: Optional[float] = None
    classification: Optional[str] = None
    hsn_sac_code: Optional[str] = None
    default_gst_rate: Optional[float] = None
    cess_percentage: Optional[float] = None
    itc_eligibility: Optional[str] = None
    is_capital_good: Optional[bool] = None
    is_perishable: Optional[bool] = None
    is_asset_fixed: Optional[bool] = None
    is_sellable: Optional[bool] = None
    track_laundry: Optional[bool] = None
    allow_partial_usage: Optional[bool] = None
    consumable_instant: Optional[bool] = None


class InventoryCategoryOut(InventoryCategoryBase):
    id: int
    created_at: datetime
    branch_id: Optional[int] = None
    branch_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# Vendor Schemas
class VendorBase(BaseModel):
    name: str  # Trade Name
    company_name: Optional[str] = None
    
    # Core GST Properties
    gst_registration_type: Optional[str] = None  # Regular, Composition, Unregistered, Overseas, SEZ
    gst_number: Optional[str] = None  # GSTIN (Mandatory for Regular)
    legal_name: Optional[str] = None  # Must match GST Portal exactly (Mandatory for Regular)
    trade_name: Optional[str] = None  # The name you know them by
    pan_number: Optional[str] = None  # 10 chars, mandatory for Unregistered/Composition
    qmp_scheme: bool = False  # Quarterly Return Monthly Payment
    msme_udyam_no: Optional[str] = None  # MSME/Udyam Registration Number
    
    # Contact Information
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    
    # Address & Place of Supply
    billing_address: Optional[str] = None  # Full address for tax invoice
    billing_state: Optional[str] = None  # For CGST/SGST vs IGST calculation
    shipping_address: Optional[str] = None  # If different from billing
    distance_km: Optional[float] = None  # For E-Way Bill generation
    
    # Legacy address fields (for backward compatibility)
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    country: Optional[str] = "India"
    
    # Compliance Settings
    is_msme_registered: bool = False  # Must pay within 45 days if True
    tds_apply: bool = False  # TDS deduction required
    rcm_applicable: bool = False  # Reverse Charge Mechanism
    
    payment_terms: Optional[str] = None
    
    # Payment & Banking Details (Critical for ITC Compliance - 180-Day Rule)
    preferred_payment_method: Optional[str] = None  # Bank Transfer, UPI, Cheque, Cash
    # Bank Account Details (For NEFT/RTGS)
    account_holder_name: Optional[str] = None  # Should match Legal Name
    bank_name: Optional[str] = None  # e.g., "HDFC Bank"
    account_number: Optional[str] = None  # 9-18 digits
    ifsc_code: Optional[str] = None  # 11 characters
    branch_name: Optional[str] = None  # Auto-fetched from IFSC
    # UPI Details (For Small/Unregistered Vendors)
    upi_id: Optional[str] = None  # e.g., shopname@okhdfcbank
    upi_mobile_number: Optional[str] = None  # 10 digits
    
    notes: Optional[str] = None
    is_active: bool = True


class VendorCreate(VendorBase):
    pass


class VendorUpdate(BaseModel):
    name: Optional[str] = None
    company_name: Optional[str] = None
    gst_registration_type: Optional[str] = None
    gst_number: Optional[str] = None
    legal_name: Optional[str] = None
    trade_name: Optional[str] = None
    pan_number: Optional[str] = None
    qmp_scheme: Optional[bool] = None
    msme_udyam_no: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    billing_address: Optional[str] = None
    billing_state: Optional[str] = None
    shipping_address: Optional[str] = None
    distance_km: Optional[float] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    country: Optional[str] = None
    is_msme_registered: Optional[bool] = None
    tds_apply: Optional[bool] = None
    rcm_applicable: Optional[bool] = None
    payment_terms: Optional[str] = None
    preferred_payment_method: Optional[str] = None
    account_holder_name: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    branch_name: Optional[str] = None
    upi_id: Optional[str] = None
    upi_mobile_number: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class VendorOut(VendorBase):
    id: int
    created_at: datetime
    updated_at: datetime
    branch_id: Optional[int] = None
    branch_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# Item Schemas
class InventoryItemBase(BaseModel):
    name: str
    item_code: Optional[str] = None
    description: Optional[str] = None
    category_id: int
    sub_category: Optional[str] = None
    hsn_code: Optional[str] = None
    unit: str = "pcs"
    min_stock_level: float = 0.0
    max_stock_level: Optional[float] = None
    unit_price: float = 0.0
    selling_price: Optional[float] = None
    gst_rate: float = 0.0
    location: Optional[str] = None
    barcode: Optional[str] = None
    image_path: Optional[str] = None
    
    # Inventory settings
    is_perishable: bool = False
    track_serial_number: bool = False
    is_sellable_to_guest: bool = False
    
    # Department-specific logic
    track_laundry_cycle: bool = False
    is_asset_fixed: bool = False
    maintenance_schedule_days: Optional[int] = None
    complimentary_limit: Optional[int] = None
    ingredient_yield_percentage: Optional[float] = None
    
    # Vendor linking
    preferred_vendor_id: Optional[int] = None
    vendor_item_code: Optional[str] = None
    lead_time_days: Optional[int] = None
    
    is_active: bool = True


class InventoryItemCreate(InventoryItemBase):
    initial_stock: Optional[float] = 0.0  # Optional initial stock when creating item


class InventoryItemUpdate(BaseModel):
    name: Optional[str] = None
    item_code: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    sub_category: Optional[str] = None
    hsn_code: Optional[str] = None
    unit: Optional[str] = None
    min_stock_level: Optional[float] = None
    max_stock_level: Optional[float] = None
    unit_price: Optional[float] = None
    selling_price: Optional[float] = None
    gst_rate: Optional[float] = None
    location: Optional[str] = None
    barcode: Optional[str] = None
    image_path: Optional[str] = None
    is_perishable: Optional[bool] = None
    track_serial_number: Optional[bool] = None
    is_sellable_to_guest: Optional[bool] = None
    track_laundry_cycle: Optional[bool] = None
    is_asset_fixed: Optional[bool] = None
    maintenance_schedule_days: Optional[int] = None
    complimentary_limit: Optional[int] = None
    ingredient_yield_percentage: Optional[float] = None
    preferred_vendor_id: Optional[int] = None
    vendor_item_code: Optional[str] = None
    lead_time_days: Optional[int] = None
    is_active: Optional[bool] = None


class InventoryItemOut(InventoryItemBase):
    id: int
    current_stock: float
    category_name: Optional[str] = None
    department: Optional[str] = None  # Department from category's parent_department
    created_at: datetime
    updated_at: datetime
    is_low_stock: bool = False
    last_purchase_price: Optional[float] = 0.0
    last_purchase_date: Optional[datetime] = None
    last_vendor_name: Optional[str] = None
    branch_id: Optional[int] = None
    branch_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# Purchase Detail Schemas
class PurchaseDetailBase(BaseModel):
    item_id: int
    hsn_code: Optional[str] = None
    quantity: float
    unit: str
    unit_price: Decimal
    gst_rate: Decimal = Decimal("0.00")
    discount: Decimal = Decimal("0.00")
    notes: Optional[str] = None


class PurchaseDetailCreate(PurchaseDetailBase):
    pass


class PurchaseDetailOut(PurchaseDetailBase):
    id: int
    purchase_master_id: int
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    total_amount: Decimal
    item_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# Purchase Master Schemas
class PurchaseMasterBase(BaseModel):
    purchase_number: str
    vendor_id: int
    purchase_date: date
    expected_delivery_date: Optional[date] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    gst_number: Optional[str] = None
    payment_terms: Optional[str] = None
    payment_status: str = "pending"
    destination_location_id: Optional[int] = None
    notes: Optional[str] = None
    status: str = "draft"


class PurchaseMasterCreate(PurchaseMasterBase):
    details: List[PurchaseDetailCreate] = []


class PurchaseMasterUpdate(BaseModel):
    purchase_number: Optional[str] = None
    vendor_id: Optional[int] = None
    purchase_date: Optional[date] = None
    expected_delivery_date: Optional[date] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    gst_number: Optional[str] = None
    payment_terms: Optional[str] = None
    payment_status: Optional[str] = None
    payment_method: Optional[str] = None  # Added missing field
    status: Optional[str] = None
    destination_location_id: Optional[int] = None
    notes: Optional[str] = None
    details: Optional[List[PurchaseDetailCreate]] = None
    
    @field_validator('payment_status', 'payment_method', mode='before')
    @classmethod
    def normalize_payment_fields(cls, v):
        """Normalize payment fields to lowercase and handle None/empty strings"""
        if v is None or (isinstance(v, str) and v.strip() == ''):
            return None
        if isinstance(v, str):
            return v.strip().lower()
        return v


class PurchaseMasterOut(PurchaseMasterBase):
    id: int
    sub_total: Decimal
    cgst: Decimal
    sgst: Decimal
    igst: Decimal
    discount: Decimal
    total_amount: Decimal
    created_by: Optional[int] = None
    created_by_name: Optional[str] = None
    vendor_name: Optional[str] = None
    vendor_gst: Optional[str] = None
    destination_location_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    details: List[PurchaseDetailOut] = []
    
    class Config:
        from_attributes = True



class StockAdjustmentCreate(BaseModel):
    location_id: int
    item_id: int
    actual_stock: float
    notes: Optional[str] = None


# Transaction Schemas
class InventoryTransactionOut(BaseModel):
    id: int
    item_id: int
    item_name: Optional[str] = None
    transaction_type: str
    quantity: float
    unit_price: Optional[float] = None
    total_amount: Optional[float] = None
    reference_number: Optional[str] = None
    purchase_master_id: Optional[int] = None
    notes: Optional[str] = None
    created_by: Optional[int] = None
    created_by_name: Optional[str] = None
    source_location_name: Optional[str] = None
    destination_location_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# Summary Schemas
class InventorySummary(BaseModel):
    total_items: int
    low_stock_items: int
    total_value: float
    categories_count: int


# Stock Requisition Schemas
class StockRequisitionDetailBase(BaseModel):
    item_id: int
    requested_quantity: float  # How much they want
    approved_quantity: Optional[float] = None  # Manager fills this
    unit: str
    notes: Optional[str] = None  # Reason (e.g., "For Weekend Buffet")


class StockRequisitionDetailCreate(StockRequisitionDetailBase):
    pass


class StockRequisitionDetailOut(StockRequisitionDetailBase):
    id: int
    item_name: Optional[str] = None
    current_stock: Optional[float] = None  # Shows current stock in Central Store
    
    class Config:
        from_attributes = True


class StockRequisitionBase(BaseModel):
    destination_department: str
    date_needed: Optional[date] = None  # When is this needed?
    priority: str = "normal"  # normal, urgent, critical
    notes: Optional[str] = None


class StockRequisitionCreate(StockRequisitionBase):
    details: List[StockRequisitionDetailCreate] = []


class StockRequisitionUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    date_needed: Optional[date] = None
    notes: Optional[str] = None
    approved_by: Optional[int] = None


class StockRequisitionOut(StockRequisitionBase):
    id: int
    requisition_number: str
    requested_by: int
    requested_by_name: Optional[str] = None
    status: str  # pending, approved, partially_issued, rejected, issued
    approved_by: Optional[int] = None
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    details: List[StockRequisitionDetailOut] = []
    
    class Config:
        from_attributes = True


# Stock Issue Schemas
class StockIssueDetailBase(BaseModel):
    item_id: int
    issued_quantity: float  # Actual amount given
    batch_lot_number: Optional[str] = None  # Critical for Restaurant (FIFO)
    unit: str
    notes: Optional[str] = None
    rental_price: Optional[float] = None  # For rentable assets like laundry
    is_damaged: Optional[bool] = False  # Track if asset is damaged
    damage_notes: Optional[str] = None  # Damage description
    is_payable: bool = False  # Track if the item is chargeable to the guest


class StockIssueDetailCreate(StockIssueDetailBase):
    pass


class StockIssueDetailOut(StockIssueDetailBase):
    id: int
    item_name: Optional[str] = None
    unit_price: Optional[float] = None
    cost: Optional[float] = None  # Calculated value of goods issued
    
    class Config:
        from_attributes = True


class StockIssueBase(BaseModel):
    requisition_id: Optional[int] = None  # Linked Req ID
    source_location_id: Optional[int] = None  # Usually "Main Warehouse"
    destination_location_id: Optional[int] = None  # Where it went
    issue_date: Optional[datetime] = None
    notes: Optional[str] = None
    booking_id: Optional[int] = None
    guest_id: Optional[int] = None


class StockIssueCreate(StockIssueBase):
    details: List[StockIssueDetailCreate] = []


class StockIssueOut(StockIssueBase):
    id: int
    issue_number: str
    issued_by: int
    issued_by_name: Optional[str] = None
    source_location_name: Optional[str] = None
    destination_location_name: Optional[str] = None
    created_at: datetime
    details: List[StockIssueDetailOut] = []
    
    class Config:
        from_attributes = True


# Waste Log Schemas
class WasteLogBase(BaseModel):
    item_id: Optional[int] = None
    food_item_id: Optional[int] = None
    is_food_item: bool = False
    location_id: Optional[int] = None  # Where did it spoil?
    batch_number: Optional[str] = None  # Links to specific Purchase Batch
    expiry_date: Optional[date] = None
    quantity: float
    unit: str
    reason_code: str  # Expired, Damaged, Spilled, Theft, Taste Test
    action_taken: Optional[str] = None  # Discarded, Returned to Vendor
    notes: Optional[str] = None


class WasteLogCreate(WasteLogBase):
    pass


class WasteLogUpdate(BaseModel):
    location_id: Optional[int] = None
    batch_number: Optional[str] = None
    expiry_date: Optional[date] = None
    quantity: Optional[float] = None
    reason_code: Optional[str] = None
    action_taken: Optional[str] = None
    notes: Optional[str] = None
    photo_path: Optional[str] = None


class WasteLogOut(WasteLogBase):
    id: int
    log_number: Optional[str] = None
    photo_path: Optional[str] = None
    reported_by: int
    reported_by_name: Optional[str] = None
    item_name: Optional[str] = None
    food_item_name: Optional[str] = None
    location_name: Optional[str] = None
    waste_date: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


# Location Schemas
class LocationBase(BaseModel):
    name: str  # "Room 101", "Main Kitchen", "Lobby", "Store A"
    building: str  # Main Block, Villas, etc.
    floor: Optional[str] = None  # Ground, 1st, 2nd, etc.
    room_area: str  # Room 101, Lobby, Conference Hall, Kitchen, etc.
    location_type: str  # Guest Room, Warehouse, Department, Public Area
    parent_location_id: Optional[int] = None  # Hierarchy (e.g., "First Floor")
    is_inventory_point: bool = False  # Can stock be stored here?
    description: Optional[str] = None
    is_active: bool = True


class LocationCreate(LocationBase):
    @field_validator('parent_location_id', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        if v == '' or v is None:
            return None
        return v


class LocationUpdate(BaseModel):
    name: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    room_area: Optional[str] = None
    location_type: Optional[str] = None
    parent_location_id: Optional[int] = None
    is_inventory_point: Optional[bool] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class LocationOut(LocationBase):
    id: int
    location_code: Optional[str] = None
    parent_location_name: Optional[str] = None
    created_at: Optional[datetime] = None
    branch_id: Optional[int] = None
    branch_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# Asset Registry Schemas (The "Profile" - tracks individual instances)
class AssetRegistryBase(BaseModel):
    item_id: int
    serial_number: Optional[str] = None  # Manufacturer's Serial No
    current_location_id: Optional[int] = None  # Where is it right now?
    status: str = "active"  # active, in_repair, damaged, written_off
    purchase_date: Optional[date] = None  # Used for depreciation
    warranty_expiry: Optional[date] = None  # Triggers Alert: "Warranty expiring in 30 days"
    last_maintenance_date: Optional[date] = None  # Triggers Logic 6.2: Safety inspection interval
    next_maintenance_due: Optional[date] = None  # When does the technician need to check it next?
    purchase_master_id: Optional[int] = None  # Link to purchase
    notes: Optional[str] = None


class AssetRegistryCreate(AssetRegistryBase):
    pass


class AssetRegistryUpdate(BaseModel):
    current_location_id: Optional[int] = None
    status: Optional[str] = None
    last_maintenance_date: Optional[date] = None
    next_maintenance_due: Optional[date] = None
    notes: Optional[str] = None


class AssetRegistryOut(AssetRegistryBase):
    id: int
    asset_tag_id: str  # Your internal sticker ID (e.g., AST-TV-014)
    item_name: Optional[str] = None
    current_location_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Asset Mapping Schemas (Legacy - kept for backward compatibility)
class AssetMappingBase(BaseModel):
    item_id: int
    location_id: int
    quantity: float = 1.0
    serial_number: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True


class AssetMappingCreate(AssetMappingBase):
    source_location_id: Optional[int] = None


class AssetMappingUpdate(BaseModel):
    location_id: Optional[int] = None
    serial_number: Optional[str] = None
    quantity: Optional[float] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    unassigned_date: Optional[datetime] = None


class AssetMappingOut(AssetMappingBase):
    id: int
    assigned_date: datetime
    assigned_by: Optional[int] = None
    assigned_by_name: Optional[str] = None
    unassigned_date: Optional[datetime] = None
    item_name: Optional[str] = None
    location_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# Laundry Schemas
class LaundryLogBase(BaseModel):
    item_id: int
    source_location_id: Optional[int] = None
    room_number: Optional[str] = None
    quantity: float
    status: str = "Incomplete Washing"
    notes: Optional[str] = None

class LaundryLogCreate(LaundryLogBase):
    pass

class LaundryLogUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    washed_at: Optional[datetime] = None
    returned_at: Optional[datetime] = None

class LaundryLogOut(LaundryLogBase):
    id: int
    item_name: Optional[str] = None
    source_location_name: Optional[str] = None
    sent_at: datetime
    washed_at: Optional[datetime] = None
    returned_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        from_attributes = True


# Inter-branch Transfer Schemas
class InterBranchTransferBase(BaseModel):
    item_id: int
    quantity: float
    source_location_id: int
    destination_branch_id: int
    destination_location_id: Optional[int] = None
    notes: Optional[str] = None


class InterBranchTransferCreate(InterBranchTransferBase):
    pass


class InterBranchTransferOut(InterBranchTransferBase):
    id: int
    source_branch_id: int
    status: str  # pending, in_transit, received, cancelled
    transfer_number: str
    created_at: datetime
    item_name: Optional[str] = None
    source_branch_name: Optional[str] = None
    destination_branch_name: Optional[str] = None
    source_location_name: Optional[str] = None
    destination_location_name: Optional[str] = None

    class Config:
        from_attributes = True


