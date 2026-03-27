# Comprehensive Checkout System - Implementation Summary

## Overview
This document describes the enhanced checkout system that acts as "Grand Central Station" pulling data from all modules (Housekeeping, Restaurant, Accounts, Inventory) to finalize guest stays.

## Features Implemented

### 1. Pre-Checkout Verification (The Audit)

#### Room Inspection Status
- **Endpoint**: `GET /bill/pre-checkout/{room_number}/verification-data`
- **Functionality**: 
  - Returns housekeeping status (pending, approved, issues_found)
  - Provides room status and booking information
  - Lists consumables with complimentary limits
  - Lists room assets that can be damaged

#### Consumables Audit
- **Logic**: Compare Actual Consumption vs. Complimentary Limit
- **Action**: If guest consumed 3 Cokes (Limit 0) → Add 3 Cokes to final bill
- **Implementation**: 
  - `process_consumables_audit()` function calculates excess consumption
  - Charges applied per unit for items consumed beyond complimentary limit
  - Automatically deducted from room inventory on checkout

#### Asset Damage Check
- **Logic**: Check for missing/broken items (Towels, Hairdryer, Remote)
- **Action**: If "Remote" is missing → Add Asset Replacement Cost to bill
- **Implementation**: 
  - `process_asset_damage_check()` function calculates replacement costs
  - Supports multiple damaged assets per room
  - Includes notes for each damage

#### Key Card Return
- **Simple checkbox** to confirm keys/access cards are returned
- **Action**: If not returned → Charge "Lost Key Fee" (default ₹50, configurable)

### 2. Financial Aggregation (Building the Bill)

#### Room Tariff Calculation
- **Days Stayed × Nightly Rate** (already implemented)
- Enhanced to handle late checkout scenarios

#### Late Checkout Fee
- **Logic**: Auto-add 50% rent if checkout is after 12:00 PM (configurable)
- **Implementation**: `calculate_late_checkout_fee()` function
- **Configurable**: `late_checkout_threshold_hour` parameter (default: 12)

#### POS Transfers (Room Service/Restaurant)
- **Any food orders** marked "Bill to Room" during the stay
- Already integrated in existing system

#### Service Charges
- **Laundry, Spa, Cab Pickups** - Already integrated

#### Advance Adjustment
- **Critical**: Deducts Advance Deposit paid during booking from Total Payable
- **Implementation**: 
  - `advance_deposit` field added to `Booking` and `PackageBooking` models
  - Automatically deducted in checkout calculation

### 3. GST & Tax Calculation (The "Smart" Engine)

#### Dynamic Room Tax
- **If Room Rate < ₹7,500** → Apply **12% GST**
- **If Room Rate ≥ ₹7,500** → Apply **18% GST**
- **Implementation**: Updated in `_calculate_bill_for_single_room()` and `_calculate_bill_for_entire_booking()`

#### Food Tax
- **5% GST** always (can be configured for 18% if composite supply)

#### GSTIN Validation
- **B2B Support**: 
  - `guest_gstin` field in checkout
  - `is_b2b` flag for B2B transactions
  - Invoice includes GSTIN for credit claims

### 4. Settlement & Payment

#### Split Payment
- **Ability to pay part Cash, part Card, part UPI**
- **Implementation**: 
  - `CheckoutPayment` model stores individual payment records
  - `split_payments` array in `CheckoutRequest` schema
  - Each payment can have transaction ID and notes

#### Discount / Coupons
- **Field**: `discount_amount` in checkout request
- **Validation**: Cannot exceed grand total
- **Applied**: After GST calculation, before advance deposit deduction

#### Tips/Gratuity
- **Field**: `tips_gratuity` in checkout request
- **Added**: To grand total (after all other calculations)

### 5. Inventory Triggers (Behind the Scenes)

#### Room Status Update
- **Room moves from Occupied → Available** (ready for housekeeping)
- Already implemented

#### Consumables Deduction
- **The consumed items are definitively removed from Room Inventory**
- **Implementation**: 
  - `deduct_room_consumables()` function
  - Creates inventory transactions for each consumed item
  - Updates `current_stock` in `InventoryItem` table

#### Linen Cycle Trigger
- **System assumes Bed Sheets & Towels are now "Dirty"**
- **Moves them to Laundry Queue**
- **Implementation**: 
  - `trigger_linen_cycle()` function
  - Creates inventory transactions with "LAUNDRY" reference
  - Tracks items with `track_laundry_cycle = True`

### 6. Documents & Outputs

#### Final Tax Invoice
- **Endpoint**: `GET /bill/checkout/{checkout_id}/invoice`
- **Includes**:
  - HSN codes (from inventory items)
  - Tax breakdown (room GST, food GST, package GST, consumables GST, asset damage GST)
  - QR code (TODO: Generate actual QR code)
  - GSTIN for B2B transactions
  - Invoice number (format: INV-YYYY-XXXXXX)

#### Gate Pass
- **Endpoint**: `GET /bill/checkout/{checkout_id}/gate-pass`
- **Purpose**: Proof of payment for Security to allow guest's car to leave
- **Includes**: Guest name, room number, checkout date, payment status

#### Guest Feedback Form
- **Endpoint**: `POST /bill/checkout/{checkout_id}/send-feedback`
- **Triggers**: Email/SMS link for review
- **Status**: Marked as `feedback_sent = True` in checkout record

## Database Schema Changes

### New Tables
1. **checkout_verifications**: Stores pre-checkout verification data per room
2. **checkout_payments**: Stores split payment records

### Enhanced Tables
1. **checkouts**: Added fields:
   - `late_checkout_fee`
   - `consumables_charges`
   - `asset_damage_charges`
   - `key_card_fee`
   - `advance_deposit`
   - `tips_gratuity`
   - `guest_gstin`
   - `is_b2b`
   - `invoice_number`
   - `invoice_pdf_path`
   - `gate_pass_path`
   - `feedback_sent`

2. **bookings**: Added `advance_deposit` field
3. **package_bookings**: Added `advance_deposit` field

## API Endpoints

### New Endpoints
1. `GET /bill/pre-checkout/{room_number}/verification-data` - Get verification data
2. `GET /bill/checkout/{checkout_id}/invoice` - Generate invoice
3. `GET /bill/checkout/{checkout_id}/gate-pass` - Generate gate pass
4. `POST /bill/checkout/{checkout_id}/send-feedback` - Send feedback form

### Enhanced Endpoints
1. `POST /bill/checkout/{room_number}` - Enhanced with all new features

## Migration

Run the migration script to add new database fields:
```sql
-- Run: ResortApp/migrations/add_checkout_enhancements.sql
```

## Frontend Integration

The frontend needs to be updated to:
1. Call `/bill/pre-checkout/{room_number}/verification-data` before checkout
2. Display consumables audit form
3. Display asset damage check form
4. Show key card return checkbox
5. Display housekeeping status
6. Show late checkout fee calculation
7. Display advance deposit and deduction
8. Support split payment input
9. Add tips/gratuity field
10. Add GSTIN input for B2B
11. Generate/download invoice after checkout
12. Generate gate pass after checkout
13. Send feedback form

## Testing Checklist

- [ ] Pre-checkout verification data retrieval
- [ ] Consumables audit calculation
- [ ] Asset damage charges
- [ ] Key card fee
- [ ] Late checkout fee (before and after 12 PM)
- [ ] Advance deposit deduction
- [ ] Split payment processing
- [ ] GST calculation (12% vs 18% for rooms)
- [ ] B2B GSTIN handling
- [ ] Inventory deduction on checkout
- [ ] Linen cycle trigger
- [ ] Invoice generation
- [ ] Gate pass generation
- [ ] Feedback form trigger

## Configuration

### Late Checkout Threshold
Default: 12:00 PM (configurable in `calculate_late_checkout_fee()`)

### Key Card Fee
Default: ₹50 (configurable in verification creation)

### GST Rates
- Room: 12% if < ₹7,500, 18% if ≥ ₹7,500
- Food: 5% (configurable)
- Package: Same as room
- Consumables: 5%
- Asset Damage: 18%

## Notes

- All calculations are done server-side for accuracy
- Inventory deductions are atomic (all or nothing)
- Split payments must sum to grand total
- Advance deposit cannot exceed grand total
- Invoice numbers are unique and auto-generated
- Room status automatically updates to "Available" (ready for housekeeping)


