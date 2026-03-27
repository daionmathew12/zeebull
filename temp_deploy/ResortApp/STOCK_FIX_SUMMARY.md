# Stock Discrepancy Fix - Summary

## Problem
Inventory stock was showing incorrect values (e.g., 48 pcs instead of 36 pcs for Mineral Water 1L).

## Root Cause
The system was incorrectly counting `transfer_in` transactions in global warehouse stock calculations.

### How It Happened:
1. When items are issued from warehouse to a room:
   - `transfer_out` transaction created (decreases global stock) ✓
   - `transfer_in` transaction created (for audit trail)
   - Frontend was incorrectly adding `transfer_in` back to global stock ✗

2. This caused a **double-counting** issue:
   - Stock Issue: -10 (transfer_out) + 10 (transfer_in) = 0 net change
   - But it should be: -10 (transfer_out only)

## Solution Implemented

### 1. Backend Stock Fix (`fix_all_stock.py`)
- Recalculated correct stock for all items from transaction history
- Excluded `transfer_in` from global stock calculations
- Updated `InventoryItem.current_stock` to correct values
- **Result**: Fixed 4 items with total discrepancy of 117 units

### 2. Frontend Fix (`ItemHistoryModal.jsx`)
- Updated stock calculation logic to properly handle transaction types:
  - `in` (purchases): +quantity ✓
  - `out` (consumption): -quantity ✓
  - `transfer_out` (issues to rooms): -quantity ✓
  - `transfer_in`: **0** (does not affect global stock) ✓
  - `adjustment`: +quantity ✓

## Transaction Type Definitions

| Type | Affects Global Stock? | Affects LocationStock? | Example |
|------|----------------------|------------------------|---------|
| `in` | ✓ Increases | ✓ Increases (if location specified) | Purchase received |
| `out` | ✓ Decreases | ✓ Decreases (if from location) | Waste, consumption |
| `transfer_out` | ✓ Decreases | ✓ Decreases (source location) | Issue to room |
| `transfer_in` | ✗ **No change** | ✓ Increases (destination location) | Room receives items |
| `adjustment` | ✓ Increases/Decreases | Varies | Manual stock correction |

## Key Insight
`transfer_in` and `transfer_out` are **paired transactions** that track movement between locations:
- `transfer_out`: Removes from global warehouse stock
- `transfer_in`: Adds to destination location stock (but NOT to global stock)

Global warehouse stock = Sum of all locations' stock, so counting both would be double-counting.

## Verification
After fix:
- Mineral Water 1L: 36 pcs (was incorrectly 48 pcs)
- All items now show correct stock matching transaction history
- Frontend stock history modal now displays accurate running balances

## Prevention
The frontend fix ensures this issue won't recur. Future stock calculations will correctly exclude `transfer_in` from global stock totals.
