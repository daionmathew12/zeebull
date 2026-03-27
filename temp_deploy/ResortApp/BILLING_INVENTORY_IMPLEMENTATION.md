# Billing Inventory Integration - Implementation Summary

## Overview
This document summarizes the implementation of billing inventory integration, which allows inventory items issued to rooms to be charged to guests during checkout.

## Changes Made

### 1. Database Model Updates (`app/models/inventory.py`)
- Added two new columns to `StockIssueDetail` table:
  - `is_payable` (Boolean): Indicates if the item should be charged to the guest
  - `is_paid` (Boolean): Tracks whether the guest has paid for the item

### 2. Schema Updates (`app/schemas/checkout.py`)
- Added `inventory_charges` field to `BillBreakdown` schema
- Added `inventory_gst` field for GST calculation on inventory charges
- Updated `inventory_usage` list to include `is_payable` and `is_paid` fields

### 3. Backend Checkout Logic (`app/api/checkout.py`)
Updated both single-room and entire-booking bill calculation functions:

**For Each Stock Issue Detail:**
- Populate `inventory_usage` list with item details including payable/paid status
- Calculate charges for items where `is_payable=True` and `is_paid=False`
- Use `selling_price` if available, otherwise `unit_price`
- Formula: `item_charge = item_price × issued_quantity`

**GST Calculation:**
- Inventory charges are taxed at 18% GST (default rate)
- Added `inventory_gst` to total GST calculation
- Added `inventory_charges` to total bill amount

### 4. Frontend Updates

#### Bookings.jsx
- Added "Food Orders" and "Services" tabs to Room Allocation Management modal
- Created `RoomFoodOrders` component to display food orders for the room
- Created `RoomServiceAssignments` component to display and assign services to the room
- Both components allow viewing existing items and creating new assignments

**Room Allocation Modal Tabs:**
1. **Inventory** - Current room inventory items with payment tracking
2. **Food Orders** - View food orders for the room, link to Food Orders page
3. **Services** - View assigned services and assign new services
4. **Add Items** - Add new inventory items to the room

## How It Works

### 1. Adding Inventory to Room
When inventory items are issued to a room via Stock Issue:
- Items are added to `StockIssueDetail` with `is_payable` flag
- `LocationStock` is automatically updated for the room
- Items appear in "Current Room Items" in the Room Allocation modal

### 2. Marking Items as Payable
In the Room Allocation Management modal:
- Items can be marked as payable/complimentary based on complimentary limits
- Payment status can be tracked (Paid/Unpaid checkbox)
- Updates are saved to `StockIssueDetail` via API

### 3. Billing Integration
During checkout (`/bill/{room_number}`):
- System fetches all `StockIssue` records for the room since check-in
- For each detail where `is_payable=True` and `is_paid=False`:
  - Calculate charge based on item price and quantity
  - Add to `inventory_charges`
  - Calculate 18% GST
- Include in total bill amount

### 4. Bill Display
The checkout bill shows:
- **Inventory Usage** section: Lists all items issued (for reference)
- **Inventory Charges**: Separate line item for payable inventory
- **GST Breakdown**: Includes inventory GST at 18%
- **Total Amount**: Includes inventory charges + GST

## Database Migration Required

**IMPORTANT:** The following database migration must be run to add the new columns:

```sql
ALTER TABLE stock_issue_details 
ADD COLUMN is_payable BOOLEAN DEFAULT FALSE,
ADD COLUMN is_paid BOOLEAN DEFAULT FALSE;
```

## API Endpoints Used

### Existing Endpoints:
- `GET /inventory/locations/{location_id}/items` - Get current room items
- `PATCH /inventory/issues/{issue_id}/details/{detail_id}` - Update payable/paid status
- `GET /bill/{room_number}` - Get bill with inventory charges

### New Components:
- `RoomFoodOrders` - Displays food orders for a room
- `RoomServiceAssignments` - Displays and manages service assignments

## Testing Checklist

1. **Add Inventory to Room:**
   - [ ] Create stock issue to room location
   - [ ] Verify items appear in Room Allocation modal
   - [ ] Check `LocationStock` is updated

2. **Mark Items as Payable:**
   - [ ] Toggle payable status in Room Allocation modal
   - [ ] Verify database is updated
   - [ ] Check complimentary limit logic

3. **Checkout with Inventory:**
   - [ ] Generate bill for room with inventory items
   - [ ] Verify inventory charges appear correctly
   - [ ] Check GST calculation (18%)
   - [ ] Confirm total amount includes inventory

4. **Payment Tracking:**
   - [ ] Mark items as paid
   - [ ] Verify paid items don't appear in charges
   - [ ] Check bill reflects payment status

5. **Food Orders Tab:**
   - [ ] View food orders for room
   - [ ] Verify filtering by room_id works
   - [ ] Test navigation to Food Orders page

6. **Services Tab:**
   - [ ] View assigned services
   - [ ] Assign new service to room
   - [ ] Verify service appears in list

## Known Limitations

1. **GST Rate:** Currently hardcoded to 18% for all inventory items. Future enhancement could use item-specific GST rates from `InventoryItem.gst_rate`.

2. **Billing.jsx:** The frontend billing page may need updates to display inventory charges in the detailed bill view and PDF generation.

3. **Price Source:** Uses `selling_price` if available, falls back to `unit_price`. Ensure items have appropriate prices set.

## Next Steps

1. **Run Database Migration:** Execute the SQL migration to add new columns
2. **Test End-to-End:** Perform complete checkout flow with inventory items
3. **Update Billing.jsx:** Add inventory charges display to bill PDF and detailed view
4. **Configure Prices:** Ensure all sellable inventory items have `selling_price` set
5. **Train Staff:** Document the workflow for marking items as payable/paid

## Files Modified

### Backend:
- `app/models/inventory.py` - Added is_payable, is_paid columns
- `app/schemas/checkout.py` - Added inventory_charges, inventory_gst fields
- `app/api/checkout.py` - Updated bill calculation logic

### Frontend:
- `dasboard/src/pages/Bookings.jsx` - Added Food Orders and Services tabs, created helper components

## Support

For questions or issues with this implementation, refer to:
- Previous session summary in conversation history
- Code comments in modified files
- This implementation summary document
