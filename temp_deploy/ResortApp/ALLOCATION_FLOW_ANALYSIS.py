"""
COMPLETE ALLOCATION FLOW ANALYSIS
==================================

1. Frontend sends allocation request to: POST /api/inventory/issues
   Payload: {
     "source_location_id": null or warehouse_id,
     "destination_location_id": room_location_id,
     "details": [
       {
         "item_id": 29,
         "quantity": 6,
         "unit": "pcs",
         "notes": "Complimentary item (1 pcs)\nPayable item (5 pcs)"
       }
     ]
   }

2. Backend (app/curd/inventory.py - create_stock_issue):
   - Auto-detects source location (if not provided)
   - Checks stock availability
   - Creates StockIssue record
   - For each detail:
     * Checks if qty > complimentary_limit
     * If yes: splits into 2 StockIssueDetail records (comp + payable)
     * If no: creates 1 StockIssueDetail record
   - Deducts from source LocationStock
   - Adds to destination LocationStock
   - Creates InventoryTransaction records

3. Frontend fetches room items from: GET /api/inventory/locations/{location_id}/items
   Response should include:
   - Items with quantities
   - Complimentary vs Payable breakdown
   - Transaction history

ISSUES TO FIX:
==============
A. Frontend doesn't send complimentary/payable split in request
B. Backend needs to read item.complimentary_limit from database
C. LocationStock update logic might not be working
D. Frontend display logic needs to aggregate StockIssueDetail.is_payable
"""
print(__doc__)
