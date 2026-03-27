from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime

class FoodOrderItem(BaseModel):
    item_name: str
    quantity: int
    amount: float
    is_paid: Optional[bool] = False
    payment_status: Optional[str] = None
    payment_method: Optional[str] = None
    payment_time: Optional[str] = None
    gst_amount: Optional[float] = 0.0
    total_with_gst: Optional[float] = 0.0

    class Config:
        from_attributes = True

class ServiceItem(BaseModel):
    service_name: str
    charges: float
    is_paid: Optional[bool] = False
    payment_status: Optional[str] = None

    class Config:
        from_attributes = True

class BillBreakdown(BaseModel):
    room_charges: Optional[float] = 0.0
    food_charges: Optional[float] = 0.0
    service_charges: Optional[float] = 0.0
    package_charges: Optional[float] = 0.0
    
    # Enhanced charges
    consumables_charges: Optional[float] = 0.0
    inventory_charges: Optional[float] = 0.0  # Charges for payable inventory items issued
    asset_damage_charges: Optional[float] = 0.0
    key_card_fee: Optional[float] = 0.0
    late_checkout_fee: Optional[float] = 0.0
    advance_deposit: Optional[float] = 0.0
    tips_gratuity: Optional[float] = 0.0
    
    # GST breakdown
    room_gst: Optional[float] = 0.0  # GST on room charges (12% if < 7500, 18% if >= 7500)
    food_gst: Optional[float] = 0.0  # GST on food charges (5% always)
    service_gst: Optional[float] = 0.0  # GST on service charges (variable, default 18%)
    package_gst: Optional[float] = 0.0  # GST on package charges (12% if < 7500, 18% if >= 7500)
    consumables_gst: Optional[float] = 0.0  # GST on consumables (5%)
    inventory_gst: Optional[float] = 0.0  # GST on inventory charges (variable, default 18%?)
    asset_damage_gst: Optional[float] = 0.0  # GST on asset damages (18%)
    total_gst: Optional[float] = 0.0  # Total GST amount
    
    # Detailed lists
    food_items: List[FoodOrderItem] = []
    service_items: List[ServiceItem] = []
    consumables_items: List[dict] = []  # Consumables charged
    asset_damages: List[dict] = []  # Asset damages
    inventory_usage: List[dict] = []  # All inventory items used/issued (Rentals)
    fixed_assets: List[dict] = []  # Fixed assets in room (for clarity)
    
    total_due: float = 0.0

class BillSummary(BaseModel):
    guest_name: str
    room_numbers: List[str]
    number_of_guests: int
    stay_nights: int
    check_in: date
    check_out: date
    charges: BillBreakdown

class CheckoutFull(BaseModel):
    id: int
    booking_id: Optional[int]
    package_booking_id: Optional[int]
    room_total: float = 0
    food_total: float = 0
    service_total: float = 0
    package_total: float = 0
    tax_amount: float = 0
    discount_amount: float = 0
    grand_total: float = 0
    payment_method: Optional[str] = ""
    payment_status: Optional[str] = "Paid"
    created_at: Optional[datetime]
    guest_name: Optional[str] = ""
    room_number: Optional[str] = ""

    class Config:
        from_attributes = True

class CheckoutDetail(BaseModel):
    id: int
    booking_id: Optional[int]
    package_booking_id: Optional[int]
    room_total: float = 0
    food_total: float = 0
    service_total: float = 0
    package_total: float = 0
    tax_amount: float = 0
    discount_amount: float = 0
    grand_total: float = 0
    payment_method: Optional[str] = ""
    payment_status: Optional[str] = "Paid"
    created_at: Optional[datetime]
    guest_name: Optional[str] = ""
    room_number: Optional[str] = ""
    food_orders: List[dict] = []
    services: List[dict] = []
    booking_details: Optional[dict] = None

    class Config:
        from_attributes = True

class CheckoutSuccess(BaseModel):
    message: str = "Checkout successful"
    checkout_id: int
    grand_total: float
    checkout_date: datetime
    
class ConsumableAuditItem(BaseModel):
    item_id: int
    item_name: str
    actual_consumed: int
    complimentary_limit: int
    charge_per_unit: float
    total_charge: float

class AssetDamageItem(BaseModel):
    asset_registry_id: Optional[int] = None
    item_id: Optional[int] = None
    item_name: str
    replacement_cost: float
    notes: Optional[str] = None
    return_location_id: Optional[int] = None
    damage_location_id: Optional[int] = None # Alias for return_location_id in some contexts
    
    # New fields for enhanced tracking
    is_laundry: Optional[bool] = False
    laundry_location_id: Optional[int] = None
    is_waste: Optional[bool] = False
    waste_location_id: Optional[int] = None
    request_replacement: Optional[bool] = False
    is_damaged: Optional[bool] = False
    is_returned: Optional[bool] = False
    return_location_id: Optional[int] = None # Ensure it exists or is clear

class RoomVerificationData(BaseModel):
    room_number: str
    housekeeping_status: str = "pending"  # pending, approved, issues_found
    housekeeping_notes: Optional[str] = None
    consumables: List[ConsumableAuditItem] = []
    asset_damages: List[AssetDamageItem] = []
    key_card_returned: bool = True

class SplitPaymentItem(BaseModel):
    payment_method: str  # cash, card, upi, bank_transfer
    amount: float
    transaction_id: Optional[str] = None
    notes: Optional[str] = None

class CheckoutRequest(BaseModel):
    payment_method: Optional[str] = Field(None, description="Single payment method (legacy support). Use split_payments for multiple methods.")
    discount_amount: Optional[float] = Field(0.0, description="Optional discount amount to be applied.")
    checkout_mode: Optional[str] = Field("multiple", description="Checkout mode: 'single' for single room checkout or 'multiple' for all rooms in booking.")
    
    # Enhanced fields
    split_payments: Optional[List[SplitPaymentItem]] = Field(None, description="Split payment across multiple methods")
    tips_gratuity: Optional[float] = Field(0.0, description="Tips/gratuity amount")
    guest_gstin: Optional[str] = Field(None, description="GSTIN for B2B invoices")
    is_b2b: Optional[bool] = Field(False, description="Is this a B2B transaction")
    
    # Pre-checkout verification
    room_verifications: Optional[List[RoomVerificationData]] = Field(None, description="Room verification data for each room")
    
    # Late checkout
    actual_checkout_time: Optional[datetime] = Field(None, description="Actual checkout time (for late checkout fee calculation)")

class InventoryCheckItem(BaseModel):
    item_id: int
    item_name: Optional[str] = None
    item_code: Optional[str] = None
    used_qty: float = 0
    missing_qty: float = 0
    damage_qty: float = 0
    allocated_stock: Optional[float] = 0.0
    is_rentable: Optional[bool] = False
    is_fixed_asset: Optional[bool] = False
    return_location_id: Optional[int] = None
    damage_location_id: Optional[int] = None
    request_replacement: Optional[bool] = False
    
    # New fields
    is_laundry: Optional[bool] = False
    laundry_location_id: Optional[int] = None
    is_waste: Optional[bool] = False
    waste_location_id: Optional[int] = None

class InventoryCheckRequest(BaseModel):
    inventory_notes: Optional[str] = None
    items: List[InventoryCheckItem] = []
    asset_damages: List[AssetDamageItem] = []
