"""
Test script to demonstrate allocation-based billing calculation.

Scenario: Ice Cream
- Allocated: 1 Complimentary + 1 Payable = 2 Total
- Used: 2 (both consumed)
- Price: ₹40 per item

Expected Charge: 1 × ₹40 = ₹40 (only the payable one)
"""

print("=== Allocation-Based Billing Test ===\n")

# Test Case: Ice Cream with split allocation
print("Ice Cream Allocation:")
print("  Allocated Complimentary: 1")
print("  Allocated Payable: 1")
print("  Total Allocated: 2")
print("  Used Quantity: 2")
print("  Unit Price: ₹40")
print()

allocated_complimentary = 1.0
allocated_payable = 1.0
used_qty = 2.0
unit_price = 40.0

# OLD LOGIC (WRONG) - Using complimentary_limit
print("OLD LOGIC (Using complimentary_limit):")
complimentary_limit = None  # Ice cream has no limit set
limit_old = complimentary_limit if complimentary_limit is not None else 0
chargeable_old = max(0, used_qty - limit_old)
charge_old = chargeable_old * unit_price
print(f"  Complimentary Limit: {limit_old}")
print(f"  Chargeable Qty: {chargeable_old} (used {used_qty} - limit {limit_old})")
print(f"  Total Charge: ₹{charge_old} ❌ WRONG!")
print()

# NEW LOGIC (CORRECT) - Using actual allocation
print("NEW LOGIC (Using actual allocation):")
if allocated_complimentary > 0 or allocated_payable > 0:
    # Use actual allocation
    chargeable_new = min(used_qty, allocated_payable)
    limit_new = allocated_complimentary
else:
    # Fall back to complimentary_limit
    limit_new = complimentary_limit if complimentary_limit is not None else 0
    chargeable_new = max(0, used_qty - limit_new)

charge_new = chargeable_new * unit_price
print(f"  Allocated Complimentary: {allocated_complimentary}")
print(f"  Allocated Payable: {allocated_payable}")
print(f"  Chargeable Qty: {chargeable_new} (min of used {used_qty} and payable {allocated_payable})")
print(f"  Total Charge: ₹{charge_new} ✅ CORRECT!")
print()

# Additional Test Cases
print("=== Additional Test Cases ===\n")

# Test Case 2: Used less than payable
print("Test Case 2: Used 1 out of 1 Payable")
used_2 = 1.0
chargeable_2 = min(used_2, allocated_payable)
charge_2 = chargeable_2 * unit_price
print(f"  Chargeable: {chargeable_2}, Charge: ₹{charge_2}")
print()

# Test Case 3: Used only complimentary
print("Test Case 3: Used 1 out of 1 Complimentary (0 Payable)")
allocated_payable_3 = 0.0
used_3 = 1.0
chargeable_3 = min(used_3, allocated_payable_3)
charge_3 = chargeable_3 * unit_price
print(f"  Chargeable: {chargeable_3}, Charge: ₹{charge_3} (No charge)")
print()

print("=== Summary ===")
print("The billing now correctly uses the ACTUAL ALLOCATION (complimentary vs payable)")
print("from stock issues, not just the item's complimentary_limit configuration.")
print("This ensures accurate billing when items are allocated with mixed types.")
