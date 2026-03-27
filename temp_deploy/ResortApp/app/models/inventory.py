from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, Text, Boolean, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class InventoryCategory(Base):
    __tablename__ = "inventory_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    # branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True, server_default="1")
    
    # branch = relationship("Branch")

    __table_args__ = (UniqueConstraint('name', name='uix_inventory_category_name'),)
    
    # Basic Identification
    parent_department = Column(String, nullable=True)  # Restaurant, Facility, Hotel, Office, Fire & Safety, Security
    gst_tax_rate = Column(Float, default=0.0, nullable=False)  # 5%, 12%, 18%, 28% - Essential for Purchase Logic
    
    # GST Classification Properties
    classification = Column(String, nullable=True)  # "Goods" or "Services"
    hsn_sac_code = Column(String, nullable=True, index=True)  # 4, 6, or 8 digits - Essential for GST Compliance
    default_gst_rate = Column(Float, default=0.0, nullable=False)  # 0%, 5%, 12%, 18%, 28%
    cess_percentage = Column(Float, default=0.0, nullable=False)  # Additional cess (e.g., 12% for aerated drinks)
    
    # ITC (Input Tax Credit) Rules
    itc_eligibility = Column(String, default="Eligible", nullable=False)  # "Eligible" or "Ineligible (Blocked)"
    is_capital_good = Column(Boolean, default=False, nullable=False)  # Capital goods have different rules
    
    # Logic Switches (The "Brain" of the System)
    is_perishable = Column(Boolean, default=False, nullable=False)  # Activates Logic 1.1: Expiry-based alerts (Vegetables, Milk, Meat)
    is_asset_fixed = Column(Boolean, default=False, nullable=False)  # Activates Logic 2.2 & 6.2: Auto-generates maintenance reminders (ACs, CCTV, Fire Extinguishers)
    is_sellable = Column(Boolean, default=False, nullable=False)  # Activates Logic 3.2: If usage exceeds limit, add charge to customer billing (Minibar drinks, Snacks)
    track_laundry = Column(Boolean, default=False, nullable=False)  # Activates Logic 5.4: Enables "Fresh -> Used -> Laundry -> Fresh" cycle (Bed sheets, Towels, Robes)
    allow_partial_usage = Column(Boolean, default=False, nullable=False)  # Activates Logic 1.2: Kitchen raises stock usage request by weight/volume (Oil, Rice)
    consumable_instant = Column(Boolean, default=False, nullable=False)  # Activates Logic 4.1: System deducts requested quantity immediately upon issuance (Office Stationery, Paper Cups)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True, nullable=False)
    
    items = relationship("InventoryItem", back_populates="category")


class Vendor(Base):
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)  # Trade Name
    company_name = Column(String, nullable=True)
    
    # Core GST Properties
    gst_registration_type = Column(String, nullable=True)  # Regular, Composition, Unregistered, Overseas, SEZ
    gst_number = Column(String, nullable=True, index=True)  # GSTIN (Mandatory for Regular)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True, server_default="1")
    
    branch = relationship("Branch")

    __table_args__ = (
        UniqueConstraint('gst_number', 'branch_id', name='uix_vendor_gst_branch'),
        UniqueConstraint('name', 'branch_id', name='uix_vendor_name_branch'),
    )
    legal_name = Column(String, nullable=True)  # Must match GST Portal exactly (Mandatory for Regular)
    trade_name = Column(String, nullable=True)  # The name you know them by
    pan_number = Column(String, nullable=True, index=True)  # 10 chars, mandatory for Unregistered/Composition
    qmp_scheme = Column(Boolean, default=False, nullable=False)  # Quarterly Return Monthly Payment
    msme_udyam_no = Column(String, nullable=True)  # MSME/Udyam Registration Number
    
    # Contact Information
    contact_person = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    
    # Address & Place of Supply
    billing_address = Column(Text, nullable=True)  # Full address for tax invoice
    billing_state = Column(String, nullable=True)  # For CGST/SGST vs IGST calculation
    shipping_address = Column(Text, nullable=True)  # If different from billing
    distance_km = Column(Float, nullable=True)  # For E-Way Bill generation
    
    # Legacy address fields (for backward compatibility)
    address = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    pincode = Column(String, nullable=True)
    country = Column(String, nullable=True, default="India")
    
    # Compliance Settings
    is_msme_registered = Column(Boolean, default=False, nullable=False)  # Must pay within 45 days if True
    tds_apply = Column(Boolean, default=False, nullable=False)  # TDS deduction required
    rcm_applicable = Column(Boolean, default=False, nullable=False)  # Reverse Charge Mechanism
    
    payment_terms = Column(String, nullable=True)  # e.g., "Net 30", "COD"
    
    # Payment & Banking Details (Critical for ITC Compliance - 180-Day Rule)
    preferred_payment_method = Column(String, nullable=True)  # Bank Transfer, UPI, Cheque, Cash
    # Bank Account Details (For NEFT/RTGS)
    account_holder_name = Column(String, nullable=True)  # Should match Legal Name
    bank_name = Column(String, nullable=True)  # e.g., "HDFC Bank"
    account_number = Column(String, nullable=True)  # 9-18 digits
    ifsc_code = Column(String, nullable=True)  # 11 characters, e.g., HDFC0001234
    branch_name = Column(String, nullable=True)  # Auto-fetched from IFSC
    # UPI Details (For Small/Unregistered Vendors)
    upi_id = Column(String, nullable=True)  # e.g., shopname@okhdfcbank
    upi_mobile_number = Column(String, nullable=True)  # 10 digits, linked mobile
    
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    purchases = relationship("PurchaseMaster", back_populates="vendor")


class InventoryItem(Base):
    __tablename__ = "inventory_items"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    item_code = Column(String, nullable=True, index=True)  # SKU/Item Code
    description = Column(Text, nullable=True)
    category_id = Column(Integer, ForeignKey("inventory_categories.id"), nullable=False)
    sub_category = Column(String, nullable=True)  # Sub-category (e.g., Meat/Dairy/Spices)
    hsn_code = Column(String, nullable=True, index=True)  # HSN/SAC code for GST
    unit = Column(String, nullable=False, default="pcs")  # pcs, kg, liter, box, etc.
    current_stock = Column(Float, default=0.0, nullable=False)
    min_stock_level = Column(Float, default=0.0, nullable=False)
    max_stock_level = Column(Float, nullable=True)
    unit_price = Column(Float, default=0.0, nullable=False)  # Purchase price
    selling_price = Column(Float, nullable=True)  # MRP/Selling price to guests
    gst_rate = Column(Float, default=0.0, nullable=False)  # GST tax rate percentage
    location = Column(String, nullable=True)  # Storage location
    barcode = Column(String, nullable=True, index=True)
    image_path = Column(String, nullable=True)  # Item image path
    
    # Inventory settings
    is_perishable = Column(Boolean, default=False, nullable=False)  # Has expiry date
    track_serial_number = Column(Boolean, default=False, nullable=False)  # Track serial numbers
    is_sellable_to_guest = Column(Boolean, default=False, nullable=False)  # Can be sold to guests
    
    # Department-specific logic
    track_laundry_cycle = Column(Boolean, default=False, nullable=False)  # For Linen items
    is_asset_fixed = Column(Boolean, default=False, nullable=False)  # Fixed asset (not consumed)
    maintenance_schedule_days = Column(Integer, nullable=True)  # Days between maintenance checks
    complimentary_limit = Column(Integer, nullable=True)  # Free items before charging
    ingredient_yield_percentage = Column(Float, nullable=True)  # Yield % for restaurant items
    
    # Vendor linking
    preferred_vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True)
    vendor_item_code = Column(String, nullable=True)  # Vendor's code for this item
    lead_time_days = Column(Integer, nullable=True)  # Days to receive after ordering
    
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True, server_default="1")
    
    # branch = relationship("Branch")

    __table_args__ = (
        UniqueConstraint('item_code', name='uix_inventory_item_code_global'),
        UniqueConstraint('barcode', name='uix_inventory_item_barcode_global'),
    )
    
    category = relationship("InventoryCategory", back_populates="items")
    preferred_vendor = relationship("Vendor", foreign_keys=[preferred_vendor_id])
    purchase_details = relationship("PurchaseDetail", back_populates="item")
    transactions = relationship("InventoryTransaction", back_populates="item")
    services = relationship(
        "Service",
        secondary="service_inventory_items",
        back_populates="inventory_items"
    )


class PurchaseMaster(Base):
    __tablename__ = "purchase_masters"
    
    id = Column(Integer, primary_key=True, index=True)
    purchase_number = Column(String, unique=True, nullable=False, index=True)  # PO Number
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    purchase_date = Column(Date, nullable=False, default=datetime.utcnow)
    expected_delivery_date = Column(Date, nullable=True)
    invoice_number = Column(String, nullable=True, index=True)
    invoice_date = Column(Date, nullable=True)
    gst_number = Column(String, nullable=True)  # Vendor GST number (can be from vendor or override)
    payment_terms = Column(String, nullable=True)
    payment_status = Column(String, default="pending", nullable=False)  # pending, partial, paid
    payment_method = Column(String, nullable=True)  # Cash, Bank Transfer, UPI, Cheque, etc.
    sub_total = Column(Numeric(10, 2), default=0.0, nullable=False)
    cgst = Column(Numeric(10, 2), default=0.0, nullable=False)  # Central GST
    sgst = Column(Numeric(10, 2), default=0.0, nullable=False)  # State GST
    igst = Column(Numeric(10, 2), default=0.0, nullable=False)  # Integrated GST (for inter-state)
    discount = Column(Numeric(10, 2), default=0.0, nullable=False)
    total_amount = Column(Numeric(10, 2), default=0.0, nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String, default="draft", nullable=False)  # draft, confirmed, received, cancelled
    destination_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)  # Where items will be stored
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True, server_default="1")
    
    branch = relationship("Branch")

    
    vendor = relationship("Vendor", back_populates="purchases")
    details = relationship("PurchaseDetail", back_populates="purchase_master", cascade="all, delete-orphan")
    destination_location = relationship("Location", foreign_keys=[destination_location_id])
    user = relationship("User", foreign_keys=[created_by])


class PurchaseDetail(Base):
    __tablename__ = "purchase_details"
    
    id = Column(Integer, primary_key=True, index=True)
    purchase_master_id = Column(Integer, ForeignKey("purchase_masters.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    hsn_code = Column(String, nullable=True)  # Can override item's HSN
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    gst_rate = Column(Numeric(5, 2), default=0.0, nullable=False)  # GST percentage (0-100)
    cgst_amount = Column(Numeric(10, 2), default=0.0, nullable=False)
    sgst_amount = Column(Numeric(10, 2), default=0.0, nullable=False)
    igst_amount = Column(Numeric(10, 2), default=0.0, nullable=False)
    discount = Column(Numeric(10, 2), default=0.0, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    notes = Column(Text, nullable=True)
    
    purchase_master = relationship("PurchaseMaster", back_populates="details")
    item = relationship("InventoryItem", back_populates="purchase_details")


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    transaction_type = Column(String, nullable=False)  # "in", "out", "adjustment", "transfer"
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=True)
    total_amount = Column(Float, nullable=True)
    reference_number = Column(String, nullable=True)  # PO number, invoice, etc.
    purchase_master_id = Column(Integer, ForeignKey("purchase_masters.id"), nullable=True)
    department = Column(String, nullable=True)  # Department that consumed/used the inventory (Restaurant, Housekeeping, etc.)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    source_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    destination_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True, server_default="1")
    
    branch = relationship("Branch")

    
    item = relationship("InventoryItem", back_populates="transactions")
    purchase_master = relationship("PurchaseMaster")
    user = relationship("User", foreign_keys=[created_by])
    source_location = relationship("Location", foreign_keys=[source_location_id])
    destination_location = relationship("Location", foreign_keys=[destination_location_id])


# Stock Requisition Model (Internal Request Flow)
class StockRequisition(Base):
    __tablename__ = "stock_requisitions"
    
    id = Column(Integer, primary_key=True, index=True)
    requisition_number = Column(String, unique=True, nullable=False, index=True)
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    destination_department = Column(String, nullable=False)  # Kitchen Main, Housekeeping, Office, etc.
    date_needed = Column(Date, nullable=True)  # When is this needed?
    priority = Column(String, default="normal", nullable=False)  # normal, urgent, critical
    status = Column(String, default="pending", nullable=False)  # pending, approved, partially_issued, rejected, issued
    notes = Column(Text, nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True, server_default="1")
    
    branch = relationship("Branch")

    
    details = relationship("StockRequisitionDetail", back_populates="requisition", cascade="all, delete-orphan")
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approved_by])


class StockRequisitionDetail(Base):
    __tablename__ = "stock_requisition_details"
    
    id = Column(Integer, primary_key=True, index=True)
    requisition_id = Column(Integer, ForeignKey("stock_requisitions.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    requested_quantity = Column(Float, nullable=False)  # How much they want
    approved_quantity = Column(Float, nullable=True)  # Manager fills this
    unit = Column(String, nullable=False)
    notes = Column(Text, nullable=True)  # Reason (e.g., "For Weekend Buffet")
    
    requisition = relationship("StockRequisition", back_populates="details")
    item = relationship("InventoryItem")


# Stock Issue Model (Approval & Deduction Flow)
class StockIssue(Base):
    __tablename__ = "stock_issues"
    
    id = Column(Integer, primary_key=True, index=True)
    issue_number = Column(String, unique=True, nullable=False, index=True)
    requisition_id = Column(Integer, ForeignKey("stock_requisitions.id"), nullable=True)  # Linked Req ID
    issued_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    source_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)  # Usually "Main Warehouse"
    destination_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)  # Where it went
    issue_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(Text, nullable=True)
    booking_id = Column(Integer, index=True, nullable=True)
    guest_id = Column(Integer, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True, server_default="1")
    
    branch = relationship("Branch")

    
    details = relationship("StockIssueDetail", back_populates="issue", cascade="all, delete-orphan")
    requisition = relationship("StockRequisition")
    issuer = relationship("User", foreign_keys=[issued_by])
    source_location = relationship("Location", foreign_keys=[source_location_id])
    destination_location = relationship("Location", foreign_keys=[destination_location_id])


class StockIssueDetail(Base):
    __tablename__ = "stock_issue_details"
    
    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("stock_issues.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    issued_quantity = Column(Float, nullable=False)  # Actual amount given
    batch_lot_number = Column(String, nullable=True)  # Critical for Restaurant (FIFO)
    unit = Column(String, nullable=False)
    unit_price = Column(Float, nullable=True)
    cost = Column(Float, nullable=True)  # Calculated value of goods issued
    notes = Column(Text, nullable=True)
    is_payable = Column(Boolean, default=False, nullable=True)  # Is this item chargeable to guest?
    is_paid = Column(Boolean, default=False, nullable=True)     # Has the guest paid for it?
    rental_price = Column(Float, nullable=True)  # Rental price for rentable assets like laundry
    is_damaged = Column(Boolean, default=False, nullable=True)  # Track if asset is damaged
    damage_notes = Column(Text, nullable=True)  # Damage description
    
    issue = relationship("StockIssue", back_populates="details")
    item = relationship("InventoryItem")


# Waste & Spoilage Log Model
class WasteLog(Base):
    __tablename__ = "waste_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    log_number = Column(String, unique=True, nullable=True, index=True)  # Unique ID
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=True)  # Made nullable
    food_item_id = Column(Integer, ForeignKey("food_items.id"), nullable=True)  # NEW
    is_food_item = Column(Boolean, default=False, nullable=False)  # NEW
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)  # Where did it spoil?
    batch_number = Column(String, nullable=True)  # Links to specific Purchase Batch
    expiry_date = Column(Date, nullable=True)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    reason_code = Column(String, nullable=False)  # Expired, Damaged, Spilled, Theft, Taste Test
    action_taken = Column(String, nullable=True)  # Discarded, Returned to Vendor
    photo_path = Column(String, nullable=True)  # Proof (Mandatory for high value)
    notes = Column(Text, nullable=True)
    reported_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    waste_date = Column(DateTime, default=datetime.utcnow, nullable=False)  # When the waste occurred
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True, server_default="1")
    
    branch = relationship("Branch")

    
    item = relationship("InventoryItem", foreign_keys=[item_id])
    food_item = relationship("FoodItem", foreign_keys=[food_item_id])  # NEW
    location = relationship("Location")
    reporter = relationship("User", foreign_keys=[reported_by])


# Location Master Model (Building, Floor, Room/Area)
class Location(Base):
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    location_code = Column(String, unique=True, nullable=True, index=True)  # e.g., LOC-RM-101
    name = Column(String, nullable=False)  # "Room 101", "Main Kitchen", "Lobby", "Store A"
    building = Column(String, nullable=False)  # Main Block, Villas, etc.
    floor = Column(String, nullable=True)  # Ground, 1st, 2nd, etc.
    room_area = Column(String, nullable=False)  # Room 101, Lobby, Conference Hall, Kitchen, etc.
    location_type = Column(String, nullable=False)  # Guest Room, Warehouse, Department, Public Area
    parent_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)  # Hierarchy (e.g., "First Floor")
    is_inventory_point = Column(Boolean, default=False, nullable=False)  # Can stock be stored here?
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True, server_default="1")
    
    branch = relationship("Branch")

    
    asset_mappings = relationship("AssetMapping", back_populates="location", cascade="all, delete-orphan")
    parent_location = relationship("Location", remote_side=[id], backref="child_locations")


# Asset Registry Model (The "Profile" - tracks individual instances)
class AssetRegistry(Base):
    __tablename__ = "asset_registry"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_tag_id = Column(String, unique=True, nullable=False, index=True)  # Your internal sticker ID (e.g., AST-TV-014)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    serial_number = Column(String, nullable=True)  # Manufacturer's Serial No (e.g., S99887766)
    current_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)  # Where is it right now?
    status = Column(String, default="active", nullable=False)  # active, in_repair, damaged, written_off
    purchase_date = Column(Date, nullable=True)  # Used for depreciation
    warranty_expiry = Column(Date, nullable=True)  # Triggers Alert: "Warranty expiring in 30 days"
    last_maintenance_date = Column(Date, nullable=True)  # Triggers Logic 6.2: Safety inspection interval
    next_maintenance_due = Column(Date, nullable=True)  # When does the technician need to check it next?
    purchase_master_id = Column(Integer, ForeignKey("purchase_masters.id"), nullable=True)  # Link to purchase
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True, server_default="1")
    
    branch = relationship("Branch")

    
    item = relationship("InventoryItem")
    current_location = relationship("Location")
    purchase_master = relationship("PurchaseMaster")


# Asset Mapping Model (Legacy - kept for backward compatibility, but AssetRegistry is the new model)
class AssetMapping(Base):
    __tablename__ = "asset_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    serial_number = Column(String, nullable=True)  # For tracking specific asset instance
    assigned_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    unassigned_date = Column(DateTime, nullable=True)
    quantity = Column(Float, default=1.0, nullable=False) # Added quantity for bulk assignment
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True, server_default="1")
    
    branch = relationship("Branch")

    
    item = relationship("InventoryItem")
    location = relationship("Location", back_populates="asset_mappings")
    assigner = relationship("User", foreign_keys=[assigned_by])


class LocationStock(Base):
    __tablename__ = "location_stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    quantity = Column(Float, default=0, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True, server_default="1")
    
    branch = relationship("Branch")

    
    location = relationship("Location")
    item = relationship("InventoryItem")


class LaundryLog(Base):
    __tablename__ = "laundry_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    source_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    room_number = Column(String, nullable=True)
    quantity = Column(Float, nullable=False)
    status = Column(String, default="Incomplete Washing", nullable=False)  # Incomplete Washing, Washed, Returned
    sent_at = Column(DateTime, default=datetime.utcnow)
    washed_at = Column(DateTime, nullable=True)
    returned_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False, index=True, server_default="1")
    
    branch = relationship("Branch")

    
    item = relationship("InventoryItem")
    source_location = relationship("Location")


class InterBranchTransfer(Base):
    __tablename__ = "inter_branch_transfers"
    
    id = Column(Integer, primary_key=True, index=True)
    transfer_number = Column(String, unique=True, nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=False)
    quantity = Column(Float, nullable=False)
    source_branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    destination_branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    source_location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    destination_location_id = Column(Integer, ForeignKey("locations.id"), nullable=True) # Linked upon receipt
    status = Column(String, default="pending", nullable=False)  # pending, in_transit, received, cancelled
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    item = relationship("InventoryItem")
    source_branch = relationship("Branch", foreign_keys=[source_branch_id])
    destination_branch = relationship("Branch", foreign_keys=[destination_branch_id])
    source_location = relationship("Location", foreign_keys=[source_location_id])
    destination_location = relationship("Location", foreign_keys=[destination_location_id])
    user = relationship("User", foreign_keys=[created_by])


