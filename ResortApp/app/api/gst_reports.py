"""
GST Reports API for GSTR-1, GSTR-3B Filing
Comprehensive GST compliance reports for resort management
"""
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from app.utils.branch_scope import get_branch_id
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, case
from typing import Optional, List, Dict, Any
from datetime import datetime, date as date_type
from pydantic import BaseModel
import io
import os

# Optional imports for GSTR-2B reconciliation (Excel parsing)
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    # print("Warning: pandas not installed. GSTR-2B reconciliation feature will be unavailable.")

from app.database import get_db
from app.utils.auth import get_current_user
from app.models.user import User
from app.models.checkout import Checkout
from app.models.booking import Booking
from app.models.Package import PackageBooking
from app.models.foodorder import FoodOrder
from app.models.service import AssignedService
from app.models.inventory import PurchaseMaster, PurchaseDetail, Vendor, InventoryCategory, InventoryItem
from app.models.expense import Expense

router = APIRouter(prefix="/gst-reports", tags=["GST Reports"])


# State Code Mapping (First 2 digits of GSTIN)
STATE_CODES = {
    "01": "Jammu and Kashmir", "02": "Himachal Pradesh", "03": "Punjab", "04": "Chandigarh",
    "05": "Uttarakhand", "06": "Haryana", "07": "Delhi", "08": "Rajasthan",
    "09": "Uttar Pradesh", "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh",
    "13": "Nagaland", "14": "Manipur", "15": "Mizoram", "16": "Tripura",
    "17": "Meghalaya", "18": "Assam", "19": "West Bengal", "20": "Jharkhand",
    "21": "Odisha", "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
    "25": "Daman and Diu", "26": "Dadra and Nagar Haveli", "27": "Maharashtra", "28": "Andhra Pradesh",
    "29": "Karnataka", "30": "Goa", "31": "Lakshadweep", "32": "Kerala",
    "33": "Tamil Nadu", "34": "Puducherry", "35": "Andaman and Nicobar Islands", "36": "Telangana",
    "37": "Andhra Pradesh (New)"
}

# Resort's State Code (Update this based on your location)
# Find your state code from STATE_CODES mapping above
# This is used to determine if supply is inter-state (IGST) or intra-state (CGST/SGST)
RESORT_STATE_CODE = "29"  # Example: Karnataka - UPDATE THIS to your actual state code

def validate_gstin(gstin: str) -> dict:
    """
    Validate GSTIN format
    Returns: {"valid": bool, "state_code": str, "state_name": str, "error": str}
    """
    if not gstin:
        return {"valid": False, "state_code": None, "state_name": None, "error": "GSTIN is required"}
    
    gstin = gstin.strip().upper()
    
    # Check length
    if len(gstin) != 15:
        return {"valid": False, "state_code": None, "state_name": None, "error": "GSTIN must be 15 characters"}
    
    # Extract state code (first 2 digits)
    state_code = gstin[:2]
    state_name = STATE_CODES.get(state_code, "Unknown State")
    
    # Basic format check: 2 digits + 10 PAN + 1 entity + 1 'Z' + 1 check digit
    # Index 13 must be 'Z' (14th character)
    if not gstin[2:12].isalnum() or gstin[12] not in "123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ" or gstin[13] != 'Z':
        return {"valid": False, "state_code": state_code, "state_name": state_name, "error": "Invalid GSTIN format"}
    
    return {"valid": True, "state_code": state_code, "state_name": state_name, "error": None}

def get_place_of_supply(gstin: str) -> str:
    """
    Get Place of Supply in format "29-Karnataka"
    """
    validation = validate_gstin(gstin)
    if validation["valid"]:
        return f"{validation['state_code']}-{validation['state_name']}"
    return "Unknown"

def is_interstate_supply(customer_state_code: str) -> bool:
    """
    Determine if supply is inter-state (different state) or intra-state (same state)
    """
    if not customer_state_code:
        return False
    return customer_state_code != RESORT_STATE_CODE

# Helper function to determine tax breakdown (CGST/SGST vs IGST)
def calculate_tax_breakdown(taxable_value: float, tax_rate: float, is_interstate: bool = False):
    """
    Calculate CGST/SGST (intra-state) or IGST (inter-state)
    """
    total_tax = taxable_value * (tax_rate / 100)
    if is_interstate:
        return {"igst": total_tax, "cgst": 0.0, "sgst": 0.0}
    else:
        half_tax = total_tax / 2
        return {"igst": 0.0, "cgst": half_tax, "sgst": half_tax}


# Helper function to get SAC code for service type
def get_room_tax_rate(room_tariff: float) -> float:
    """
    Get GST rate for room based on tariff slab (per night)
    - Rooms < Rs.5,000: 5% GST
    - Rooms Rs.5,000 - Rs.7,499: 12% GST
    - Rooms >= Rs.7,500: 18% GST
    """
    if room_tariff < 5000:
        return 5.0
    elif room_tariff <= 7500:
        return 12.0
    else:
        return 18.0

def get_sac_code(service_type: str) -> str:
    """Map service types to SAC codes"""
    sac_mapping = {
        "room": "9963",  # Accommodation Services
        "food": "996331",  # Restaurant Services
        "spa": "999599",  # Spa Services
        "event": "999599",  # Event Services
        "service": "999599",  # Other Services
    }
    return sac_mapping.get(service_type.lower(), "999599")


@router.get("/b2b-sales")
def get_b2b_sales_register(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    branch_id: Optional[int] = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """
    B2B Sales Register - Invoices issued to customers with GSTIN
    Required for GSTR-1 Table 4A
    
    Returns invoices broken down by tax rate (multiple rows per invoice if different rates)
    Each row represents one tax rate component of the invoice.
    """
    try:
        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            try:
                if len(start_date) == 10:
                    date_obj = date_type.fromisoformat(start_date)
                    start_dt = datetime.combine(date_obj, datetime.min.time())
                else:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except:
                start_dt = None
        if end_date:
            try:
                if len(end_date) == 10:
                    date_obj = date_type.fromisoformat(end_date)
                    end_dt = datetime.combine(date_obj, datetime.max.time())
                else:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except:
                end_dt = None

        # Query checkouts with GSTIN (B2B) - Optimized with limit
        query = (db.query(Checkout).filter(Checkout.branch_id == branch_id) if branch_id is not None else db.query(Checkout)).filter(
            and_(
                Checkout.is_b2b == True,
                Checkout.guest_gstin.isnot(None),
                Checkout.guest_gstin != ""
            )
        )
        if branch_id is not None:
            query = query.filter(Checkout.branch_id == branch_id)
        if start_dt:
            query = query.filter(Checkout.checkout_date >= start_dt)
        if end_dt:
            query = query.filter(Checkout.checkout_date <= end_dt)

        checkouts = query.order_by(Checkout.checkout_date).limit(500).all()

        b2b_sales = []
        invalid_gstin_count = 0
        
        for c in checkouts:
            # Validate GSTIN
            gstin_validation = validate_gstin(c.guest_gstin)
            if not gstin_validation["valid"]:
                invalid_gstin_count += 1
                # print(f"Warning: Invalid GSTIN {c.guest_gstin} for checkout {c.id}: {gstin_validation['error']}")
                continue
            
            # Get place of supply
            place_of_supply = get_place_of_supply(c.guest_gstin)
            customer_state_code = gstin_validation["state_code"]
            is_interstate = is_interstate_supply(customer_state_code)
            
            # Invoice header data (same for all rows of this invoice)
            invoice_date = c.checkout_date
            invoice_number = c.invoice_number or f"INV-{c.id:06d}"
            invoice_value = float(c.grand_total or 0)
            receiver_name = c.guest_name or "Unknown"
            gstin = c.guest_gstin.upper()
            
            # Break down invoice by service type and tax rate
            # Room Services: 12% if < Rs.7,500, 18% if >= Rs.7,500
            room_total = float(c.room_total or 0)
            if room_total > 0:
                # Calculate nights to get daily rate
                nights = 1
                if c.booking and c.booking.check_in and c.booking.check_out:
                    delta = (c.booking.check_out - c.booking.check_in).days
                    nights = max(1, delta)
                elif c.package_booking and c.package_booking.check_in and c.package_booking.check_out:
                    delta = (c.package_booking.check_out - c.package_booking.check_in).days
                    nights = max(1, delta)
                
                daily_rate = room_total / nights
                room_tax_rate = get_room_tax_rate(daily_rate)
                
                # room_total is exclusive of tax (taxable value)
                room_taxable = room_total
                tax_breakdown = calculate_tax_breakdown(room_taxable, room_tax_rate, is_interstate)
                
                b2b_sales.append({
                    "gstin": gstin,
                    "receiver_name": receiver_name,
                    "invoice_number": invoice_number,
                    "invoice_date": invoice_date.strftime("%d-%b-%Y") if invoice_date else None,
                    "invoice_value": round(invoice_value, 2),
                    "place_of_supply": place_of_supply,
                    "reverse_charge": "No",  # Usually No for hotels
                    "invoice_type": "Regular",  # Regular, SEZ Supplies (With Payment), SEZ Supplies (Without Payment)
                    "ecommerce_gstin": "",  # If sold through e-commerce platform
                    "rate": round(room_tax_rate, 2),
                    "taxable_value": round(room_taxable, 2),
                    "igst": round(tax_breakdown["igst"], 2),
                    "cgst": round(tax_breakdown["cgst"], 2),
                    "sgst": round(tax_breakdown["sgst"], 2),
                    "cess": 0.0,  # Add if applicable (e.g., luxury tax)
                    "description": "Accommodation Services (SAC 9963)"
                })
            
            # Food Services: 5% GST
            food_total = float(c.food_total or 0)
            if food_total > 0:
                food_tax_rate = 5.0
                # food_total is exclusive of tax
                food_taxable = food_total
                tax_breakdown = calculate_tax_breakdown(food_taxable, food_tax_rate, is_interstate)
                
                b2b_sales.append({
                    "gstin": gstin,
                    "receiver_name": receiver_name,
                    "invoice_number": invoice_number,  # Same invoice number
                    "invoice_date": invoice_date.strftime("%d-%b-%Y") if invoice_date else None,
                    "invoice_value": round(invoice_value, 2),  # Same invoice value
                    "place_of_supply": place_of_supply,
                    "reverse_charge": "No",
                    "invoice_type": "Regular",
                    "ecommerce_gstin": "",
                    "rate": round(food_tax_rate, 2),
                    "taxable_value": round(food_taxable, 2),
                    "igst": round(tax_breakdown["igst"], 2),
                    "cgst": round(tax_breakdown["cgst"], 2),
                    "sgst": round(tax_breakdown["sgst"], 2),
                    "cess": 0.0,
                    "description": "Restaurant Services (SAC 996331)"
                })
            
            # Service Charges: 18% GST (typically)
            service_total = float(c.service_total or 0)
            if service_total > 0:
                service_tax_rate = 18.0
                # service_total is exclusive of tax
                service_taxable = service_total
                tax_breakdown = calculate_tax_breakdown(service_taxable, service_tax_rate, is_interstate)
                
                b2b_sales.append({
                    "gstin": gstin,
                    "receiver_name": receiver_name,
                    "invoice_number": invoice_number,
                    "invoice_date": invoice_date.strftime("%d-%b-%Y") if invoice_date else None,
                    "invoice_value": round(invoice_value, 2),
                    "place_of_supply": place_of_supply,
                    "reverse_charge": "No",
                    "invoice_type": "Regular",
                    "ecommerce_gstin": "",
                    "rate": round(service_tax_rate, 2),
                    "taxable_value": round(service_taxable, 2),
                    "igst": round(tax_breakdown["igst"], 2),
                    "cgst": round(tax_breakdown["cgst"], 2),
                    "sgst": round(tax_breakdown["sgst"], 2),
                    "cess": 0.0,
                    "description": "Other Services (SAC 999599)"
                })
            
            # Package Services: Use room rate logic
            package_total = float(c.package_total or 0)
            if package_total > 0:
                # Calculate nights to get daily rate
                nights = 1
                if c.booking and c.booking.check_in and c.booking.check_out:
                    delta = (c.booking.check_out - c.booking.check_in).days
                    nights = max(1, delta)
                elif c.package_booking and c.package_booking.check_in and c.package_booking.check_out:
                    delta = (c.package_booking.check_out - c.package_booking.check_in).days
                    nights = max(1, delta)
                
                daily_rate = package_total / nights
                package_tax_rate = 12.0 if daily_rate <= 7500 else 18.0
                if daily_rate < 5000:
                    package_tax_rate = 5.0
                    
                # package_total is exclusive of tax
                package_taxable = package_total
                tax_breakdown = calculate_tax_breakdown(package_taxable, package_tax_rate, is_interstate)
                
                b2b_sales.append({
                    "gstin": gstin,
                    "receiver_name": receiver_name,
                    "invoice_number": invoice_number,
                    "invoice_date": invoice_date.strftime("%d-%b-%Y") if invoice_date else None,
                    "invoice_value": round(invoice_value, 2),
                    "place_of_supply": place_of_supply,
                    "reverse_charge": "No",
                    "invoice_type": "Regular",
                    "ecommerce_gstin": "",
                    "rate": round(package_tax_rate, 2),
                    "taxable_value": round(package_taxable, 2),
                    "igst": round(tax_breakdown["igst"], 2),
                    "cgst": round(tax_breakdown["cgst"], 2),
                    "sgst": round(tax_breakdown["sgst"], 2),
                    "cess": 0.0,
                    "description": "Package Services (SAC 9963)"
                })

        return {
            "period": {"start_date": start_date, "end_date": end_date},
            "total_records": len(b2b_sales),
            "total_invoices": len(set([s["invoice_number"] for s in b2b_sales])),
            "invalid_gstin_count": invalid_gstin_count,
            "total_taxable_value": sum([s["taxable_value"] for s in b2b_sales]),
            "total_igst": sum([s["igst"] for s in b2b_sales]),
            "total_cgst": sum([s["cgst"] for s in b2b_sales]),
            "total_sgst": sum([s["sgst"] for s in b2b_sales]),
            "total_cess": sum([s["cess"] for s in b2b_sales]),
            "data": b2b_sales
        }
    except Exception as e:
        import traceback
        print(f"Error in B2B Sales Register: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error generating B2B Sales Register: {str(e)}")


@router.get("/b2c-sales")
def get_b2c_sales_register(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    branch_id: Optional[int] = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """
    B2C Sales Register - Consolidated bills for customers without GSTIN
    Returns both B2C Large (Inter-state >Rs.2.5L, invoice-by-invoice) and B2C Small (grouped by state and tax rate)
    Required for GSTR-1 Table 5 (B2C Large) and Table 7 (B2C Small)
    """
    try:
        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            try:
                if len(start_date) == 10:
                    date_obj = date_type.fromisoformat(start_date)
                    start_dt = datetime.combine(date_obj, datetime.min.time())
                else:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except:
                start_dt = None
        if end_date:
            try:
                if len(end_date) == 10:
                    date_obj = date_type.fromisoformat(end_date)
                    end_dt = datetime.combine(date_obj, datetime.max.time())
                else:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except:
                end_dt = None

        # Query checkouts without GSTIN (B2C) - not B2B
        query = (db.query(Checkout).filter(Checkout.branch_id == branch_id) if branch_id is not None else db.query(Checkout)).filter(
            or_(
                Checkout.is_b2b == False,
                Checkout.is_b2b == None,
                and_(
                    Checkout.guest_gstin.is_(None),
                    Checkout.guest_gstin == ""
                )
            )
        )
        if branch_id is not None:
            query = query.filter(Checkout.branch_id == branch_id)
        if start_dt:
            query = query.filter(Checkout.checkout_date >= start_dt)
        if end_dt:
            query = query.filter(Checkout.checkout_date <= end_dt)

        checkouts = query.order_by(Checkout.checkout_date).limit(500).all()

        b2c_large = []  # Inter-state invoices > Rs.2.5L (invoice-by-invoice)
        b2c_small = {}  # All other sales (grouped by Place of Supply and Tax Rate)
        
        # TODO: Add guest_state field to Checkout model to determine Place of Supply
        # For now, we'll use a default assumption or extract from booking if available
        # Default: Assume intra-state (resort's state) unless specified otherwise

        for c in checkouts:
            invoice_date = c.checkout_date
            invoice_number = c.invoice_number or f"INV-{c.id:06d}"
            invoice_value = float(c.grand_total or 0)
            
            # Determine Place of Supply
            # TODO: Get from guest address or booking source
            # For now, assume intra-state (resort's state) for most cases
            # If you have guest address/state info, extract it here
            place_of_supply_code = RESORT_STATE_CODE  # Default: Resort's state
            place_of_supply = f"{RESORT_STATE_CODE}-{STATE_CODES.get(RESORT_STATE_CODE, 'Unknown')}"
            is_interstate = False  # Default: intra-state
            
            # TODO: If booking source is OTA, get E-Commerce GSTIN
            # For now, leave empty - can be enhanced when booking source tracking is added
            ecommerce_gstin = ""
            
            # Break down invoice by service type and tax rate (same as B2B)
            invoice_rows = []
            
            # Room Services
            room_total = float(c.room_total or 0)
            if room_total > 0:
                # Calculate nights
                nights = 1
                if c.booking and c.booking.check_in and c.booking.check_out:
                    delta = (c.booking.check_out - c.booking.check_in).days
                    nights = max(1, delta)
                elif c.package_booking and c.package_booking.check_in and c.package_booking.check_out:
                    delta = (c.package_booking.check_out - c.package_booking.check_in).days
                    nights = max(1, delta)
                
                daily_rate = room_total / nights
                room_tax_rate = get_room_tax_rate(daily_rate)
                
                # room_total is exclusive of tax
                room_taxable = room_total
                tax_breakdown = calculate_tax_breakdown(room_taxable, room_tax_rate, is_interstate)
                invoice_rows.append({
                    "rate": room_tax_rate,
                    "taxable_value": room_taxable,
                    "igst": tax_breakdown["igst"],
                    "cgst": tax_breakdown["cgst"],
                    "sgst": tax_breakdown["sgst"],
                    "cess": 0.0
                })
            
            # Food Services
            food_total = float(c.food_total or 0)
            if food_total > 0:
                food_tax_rate = 5.0
                food_taxable = food_total
                tax_breakdown = calculate_tax_breakdown(food_taxable, food_tax_rate, is_interstate)
                invoice_rows.append({
                    "rate": food_tax_rate,
                    "taxable_value": food_taxable,
                    "igst": tax_breakdown["igst"],
                    "cgst": tax_breakdown["cgst"],
                    "sgst": tax_breakdown["sgst"],
                    "cess": 0.0
                })
            
            # Service Charges
            service_total = float(c.service_total or 0)
            if service_total > 0:
                service_tax_rate = 18.0
                service_taxable = service_total
                tax_breakdown = calculate_tax_breakdown(service_taxable, service_tax_rate, is_interstate)
                invoice_rows.append({
                    "rate": service_tax_rate,
                    "taxable_value": service_taxable,
                    "igst": tax_breakdown["igst"],
                    "cgst": tax_breakdown["cgst"],
                    "sgst": tax_breakdown["sgst"],
                    "cess": 0.0
                })
            
            # Package Services
            package_total = float(c.package_total or 0)
            if package_total > 0:
                # Calculate nights
                nights = 1
                if c.booking and c.booking.check_in and c.booking.check_out:
                    delta = (c.booking.check_out - c.booking.check_in).days
                    nights = max(1, delta)
                elif c.package_booking and c.package_booking.check_in and c.package_booking.check_out:
                    delta = (c.package_booking.check_out - c.package_booking.check_in).days
                    nights = max(1, delta)
                
                daily_rate = package_total / nights
                package_tax_rate = 12.0 if daily_rate <= 7500 else 18.0
                if daily_rate < 5000:
                    package_tax_rate = 5.0
                    
                package_taxable = package_total
                tax_breakdown = calculate_tax_breakdown(package_taxable, package_tax_rate, is_interstate)
                invoice_rows.append({
                    "rate": package_tax_rate,
                    "taxable_value": package_taxable,
                    "igst": tax_breakdown["igst"],
                    "cgst": tax_breakdown["cgst"],
                    "sgst": tax_breakdown["sgst"],
                    "cess": 0.0
                })
            
            # Calculate total taxable value for this invoice
            total_taxable = sum([row["taxable_value"] for row in invoice_rows])
            
            # B2C Large: Inter-state AND Invoice Value > Rs.2.5L
            if is_interstate and invoice_value > 250000:
                # Report invoice-by-invoice (one row per tax rate)
                for row in invoice_rows:
                    b2c_large.append({
                        "invoice_number": invoice_number,
                        "invoice_date": invoice_date.strftime("%d-%b-%Y") if invoice_date else None,
                        "invoice_value": round(invoice_value, 2),
                        "place_of_supply": place_of_supply,
                        "rate": round(row["rate"], 2),
                        "taxable_value": round(row["taxable_value"], 2),
                        "igst": round(row["igst"], 2),
                        "cgst": round(row["cgst"], 2),
                        "sgst": round(row["sgst"], 2),
                        "cess": round(row["cess"], 2)
                    })
            else:
                # B2C Small: Group by Place of Supply and Tax Rate
                # Track which invoices have been counted in which groups
                # (An invoice can appear in multiple groups if it has different tax rates)
                for row in invoice_rows:
                    key = f"{place_of_supply}_{row['rate']}%_{ecommerce_gstin}"
                    if key not in b2c_small:
                        b2c_small[key] = {
                            "place_of_supply": place_of_supply,
                            "rate": row["rate"],
                            "taxable_value": 0.0,
                            "igst": 0.0,
                            "cgst": 0.0,
                            "sgst": 0.0,
                            "cess": 0.0,
                            "ecommerce_gstin": ecommerce_gstin if ecommerce_gstin else "",
                            "invoice_count": set()  # Track unique invoices in this group
                        }
                    b2c_small[key]["taxable_value"] += row["taxable_value"]
                    b2c_small[key]["igst"] += row["igst"]
                    b2c_small[key]["cgst"] += row["cgst"]
                    b2c_small[key]["sgst"] += row["sgst"]
                    b2c_small[key]["cess"] += row["cess"]
                    # Track invoice in this group
                    b2c_small[key]["invoice_count"].add(invoice_number)
        
        # Round all values in b2c_small and convert invoice_count set to integer
        for key in b2c_small:
            for field in ["taxable_value", "igst", "cgst", "sgst", "cess"]:
                b2c_small[key][field] = round(b2c_small[key][field], 2)
            # Convert set to count
            b2c_small[key]["invoice_count"] = len(b2c_small[key]["invoice_count"])

        return {
            "period": {"start_date": start_date, "end_date": end_date},
            "b2c_large": {
                "description": "Inter-State Invoices > Rs.2.5L (Invoice-by-Invoice)",
                "total_records": len(b2c_large),
                "total_invoices": len(set([item["invoice_number"] for item in b2c_large])),
                "data": b2c_large
            },
            "b2c_small": {
                "description": "All Other Sales (Grouped by Place of Supply & Tax Rate)",
                "total_groups": len(b2c_small),
                "data": list(b2c_small.values())
            },
            "summary": {
                "total_b2c_large_taxable": sum([item["taxable_value"] for item in b2c_large]),
                "total_b2c_small_taxable": sum([item["taxable_value"] for item in b2c_small.values()]),
                "total_b2c_large_igst": sum([item["igst"] for item in b2c_large]),
                "total_b2c_small_igst": sum([item["igst"] for item in b2c_small.values()]),
                "total_b2c_large_cgst": sum([item["cgst"] for item in b2c_large]),
                "total_b2c_small_cgst": sum([item["cgst"] for item in b2c_small.values()]),
                "total_b2c_large_sgst": sum([item["sgst"] for item in b2c_large]),
                "total_b2c_small_sgst": sum([item["sgst"] for item in b2c_small.values()])
            }
        }
    except Exception as e:
        import traceback
        print(f"Error in B2C Sales Register: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error generating B2C Sales Register: {str(e)}")


@router.get("/hsn-sac-summary")
def get_hsn_sac_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    branch_id: Optional[int] = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """
    Get HSN/SAC Summary Report for GSTR-1 filing
    Groups all sales (rooms, food, services, packages, consumables) by HSN/SAC code
    
    HSN/SAC Summary Report - What you sold, grouped by HSN/SAC code
    Required for GSTR-1 Table 12
    
    Groups all sales by HSN/SAC code and aggregates:
    - Total Quantity
    - Total Value (including tax)
    - Taxable Value (before tax)
    - IGST, CGST, SGST, Cess
    
    Common Resort Codes:
    - SAC 9963: Accommodation Services (Room Rent)
    - SAC 996331: Restaurant & Food Services
    - SAC 9997: Other Services (Spa, Laundry, Games)
    """
    try:
        # Parse dates - convert to date objects for consistent filtering
        start_dt = None
        end_dt = None
        if start_date:
            try:
                if len(start_date) == 10:
                    start_dt = date_type.fromisoformat(start_date)
                else:
                    dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    start_dt = dt.date() if isinstance(dt, datetime) else dt
            except Exception as e:
                # print(f"HSN/SAC Summary: Error parsing start_date {start_date}: {str(e)}")
                start_dt = None
        if end_date:
            try:
                if len(end_date) == 10:
                    end_dt = date_type.fromisoformat(end_date)
                else:
                    dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    end_dt = dt.date() if isinstance(dt, datetime) else dt
            except Exception as e:
                # print(f"HSN/SAC Summary: Error parsing end_date {end_date}: {str(e)}")
                end_dt = None

        # Query ALL checkouts with booking relationships to get actual nights
        # Remove limit to get all data - this is critical for accurate reporting
        # Use outerjoin to handle cases where booking/package_booking might not exist
        try:
            query = (db.query(Checkout).filter(Checkout.branch_id == branch_id) if branch_id is not None else db.query(Checkout)).options(
                joinedload(Checkout.booking),
                joinedload(Checkout.package_booking)
            )
            if branch_id is not None:
                query = query.filter(Checkout.branch_id == branch_id)
            # Filter by date (SQLAlchemy handles datetime vs date comparison automatically)
            if start_dt:
                query = query.filter(Checkout.checkout_date >= start_dt)
            if end_dt:
                query = query.filter(Checkout.checkout_date <= end_dt)
            
            # Order by checkout date for consistency
            query = query.order_by(Checkout.checkout_date.desc())
            
            # Get all checkouts - no limit for accurate reporting
            checkouts = query.all()
        except Exception as query_error:
            # print(f"HSN/SAC Summary: Error in query - {str(query_error)}")
            import traceback
            traceback.print_exc()
            # Fallback: query without eager loading
            query = (db.query(Checkout).filter(Checkout.branch_id == branch_id) if branch_id is not None else db.query(Checkout))
            if start_dt:
                query = query.filter(Checkout.checkout_date >= start_dt)
            if end_dt:
                query = query.filter(Checkout.checkout_date <= end_dt)
            query = query.order_by(Checkout.checkout_date.desc())
            checkouts = query.all()
        
        # Debug: Log checkout count
        # print(f"HSN/SAC Summary: Found {len(checkouts)} checkouts")

        # Group by HSN/SAC code and tax rate
        # Key: (hsn_sac_code, tax_rate)
        hsn_summary = {}
        
        room_count = 0
        food_count = 0
        service_count = 0
        package_count = 0
        consumables_count = 0
        
        for c in checkouts:
            # Calculate nights for room revenue
            nights = 1  # Default to 1 if booking not found
            try:
                if c.booking and hasattr(c.booking, 'check_in') and hasattr(c.booking, 'check_out'):
                    if c.booking.check_in and c.booking.check_out:
                        delta = (c.booking.check_out - c.booking.check_in).days
                        nights = max(1, delta) if delta > 0 else 1
                elif c.package_booking and hasattr(c.package_booking, 'check_in') and hasattr(c.package_booking, 'check_out'):
                    if c.package_booking.check_in and c.package_booking.check_out:
                        delta = (c.package_booking.check_out - c.package_booking.check_in).days
                        nights = max(1, delta) if delta > 0 else 1
            except (AttributeError, TypeError) as e:
                print(f"Error calculating nights for checkout {c.id}: {str(e)}")
                nights = 1  # Fallback to 1 night
            
            # Room Services (SAC 9963) - Accommodation Services
            room_total = float(c.room_total or 0)
            if room_total > 0:
                room_count += 1
                sac_code = "9963"
                
                daily_rate = room_total / nights
                tax_rate = get_room_tax_rate(daily_rate)
                
                taxable_value = room_total
                total_value = taxable_value * (1 + tax_rate / 100)
                total_tax = total_value - taxable_value
                
                key = f"{sac_code}_{tax_rate}%"
                if key not in hsn_summary:
                    hsn_summary[key] = {
                        "hsn_sac_code": sac_code,
                        "description": "Accommodation Services (Room Rent)",
                        "uqc": "NOS",  # Numbers (Nights)
                        "quantity": 0,
                        "total_value": 0.0,  # Grand total including tax
                        "taxable_value": 0.0,
                        "integrated_tax": 0.0,  # IGST
                        "central_tax": 0.0,  # CGST
                        "state_ut_tax": 0.0,  # SGST
                        "cess_amount": 0.0,
                        "tax_rate": tax_rate
                    }
                
                hsn_summary[key]["quantity"] += nights
                hsn_summary[key]["total_value"] += total_value
                hsn_summary[key]["taxable_value"] += taxable_value
                
                # Calculate tax breakdown (assuming intra-state for now)
                is_interstate = False  # Can be enhanced with guest state
                tax_breakdown = calculate_tax_breakdown(taxable_value, tax_rate, is_interstate)
                hsn_summary[key]["integrated_tax"] += tax_breakdown["igst"]
                hsn_summary[key]["central_tax"] += tax_breakdown["cgst"]
                hsn_summary[key]["state_ut_tax"] += tax_breakdown["sgst"]

            # Food Services (SAC 996331) - Restaurant & Food Services
            food_total = float(c.food_total or 0)
            if food_total > 0:
                food_count += 1
                sac_code = "996331"
                tax_rate = 5.0  # Restaurant services 5% GST
                taxable_value = food_total
                total_value = taxable_value * (1 + tax_rate / 100)
                total_tax = total_value - taxable_value
                
                key = f"{sac_code}_{tax_rate}%"
                if key not in hsn_summary:
                    hsn_summary[key] = {
                        "hsn_sac_code": sac_code,
                        "description": "Restaurant & Food Services",
                        "uqc": "UNIT",  # Units (items/orders)
                        "quantity": 0,
                        "total_value": 0.0,
                        "taxable_value": 0.0,
                        "integrated_tax": 0.0,
                        "central_tax": 0.0,
                        "state_ut_tax": 0.0,
                        "cess_amount": 0.0,
                        "tax_rate": tax_rate
                    }
                
                # Count food orders (can be enhanced to count actual items)
                hsn_summary[key]["quantity"] += 1
                hsn_summary[key]["total_value"] += total_value
                hsn_summary[key]["taxable_value"] += taxable_value
                
                tax_breakdown = calculate_tax_breakdown(taxable_value, tax_rate, False)
                hsn_summary[key]["integrated_tax"] += tax_breakdown["igst"]
                hsn_summary[key]["central_tax"] += tax_breakdown["cgst"]
                hsn_summary[key]["state_ut_tax"] += tax_breakdown["sgst"]

            # Other Services (SAC 9997) - Spa, Laundry, Games, etc.
            service_total = float(c.service_total or 0)
            if service_total > 0:
                service_count += 1
                sac_code = "9997"
                tax_rate = 18.0  # Other services typically 18%
                taxable_value = service_total
                total_value = taxable_value * (1 + tax_rate / 100)
                total_tax = total_value - taxable_value
                
                key = f"{sac_code}_{tax_rate}%"
                if key not in hsn_summary:
                    hsn_summary[key] = {
                        "hsn_sac_code": sac_code,
                        "description": "Other Services (Spa, Laundry, Games, etc.)",
                        "uqc": "UNIT",
                        "quantity": 0,
                        "total_value": 0.0,
                        "taxable_value": 0.0,
                        "integrated_tax": 0.0,
                        "central_tax": 0.0,
                        "state_ut_tax": 0.0,
                        "cess_amount": 0.0,
                        "tax_rate": tax_rate
                    }
                
                hsn_summary[key]["quantity"] += 1
                hsn_summary[key]["total_value"] += total_value
                hsn_summary[key]["taxable_value"] += taxable_value
                
                tax_breakdown = calculate_tax_breakdown(taxable_value, tax_rate, False)
                hsn_summary[key]["integrated_tax"] += tax_breakdown["igst"]
                hsn_summary[key]["central_tax"] += tax_breakdown["cgst"]
                hsn_summary[key]["state_ut_tax"] += tax_breakdown["sgst"]

            # Package Services (SAC 9963 or 9997 depending on package type)
            # For simplicity, treating as Accommodation if room-based, else Other Services
            package_total = float(c.package_total or 0)
            if package_total > 0:
                package_count += 1
                # If package includes room, use SAC 9963, else 9997
                sac_code = "9963" if room_total > 0 else "9997"
                
                daily_rate = package_total / nights
                tax_rate = 12.0 if daily_rate <= 7500 else 18.0
                if daily_rate < 5000:
                    tax_rate = 5.0
                    
                taxable_value = package_total
                total_value = taxable_value * (1 + tax_rate / 100)
                total_tax = total_value - taxable_value
                
                key = f"{sac_code}_package_{tax_rate}%"
                if key not in hsn_summary:
                    hsn_summary[key] = {
                        "hsn_sac_code": sac_code,
                        "description": f"Package Services ({'Accommodation' if sac_code == '9963' else 'Other Services'})",
                        "uqc": "UNIT",
                        "quantity": 0,
                        "total_value": 0.0,
                        "taxable_value": 0.0,
                        "integrated_tax": 0.0,
                        "central_tax": 0.0,
                        "state_ut_tax": 0.0,
                        "cess_amount": 0.0,
                        "tax_rate": tax_rate
                    }
                
                hsn_summary[key]["quantity"] += 1
                hsn_summary[key]["total_value"] += total_value
                hsn_summary[key]["taxable_value"] += taxable_value
                
                tax_breakdown = calculate_tax_breakdown(taxable_value, tax_rate, False)
                hsn_summary[key]["integrated_tax"] += tax_breakdown["igst"]
                hsn_summary[key]["central_tax"] += tax_breakdown["cgst"]
                hsn_summary[key]["state_ut_tax"] += tax_breakdown["sgst"]

        # Process Inventory Items sold to guests (Consumables)
        # Wrap in try-except to prevent crashes if consumables_audit_data column doesn't exist or has issues
        try:
            # Check if consumables_audit_data column exists
            from sqlalchemy import inspect
            checkout_inspector = inspect(Checkout)
            has_consumables_column = 'consumables_audit_data' in [col.name for col in checkout_inspector.columns]
            
            if has_consumables_column:
                # Query checkouts with consumables_audit_data
                consumables_query = (db.query(Checkout).filter(Checkout.branch_id == branch_id) if branch_id is not None else db.query(Checkout)).filter(Checkout.consumables_audit_data.isnot(None))
                if start_dt:
                    consumables_query = consumables_query.filter(Checkout.checkout_date >= start_dt)
                if end_dt:
                    consumables_query = consumables_query.filter(Checkout.checkout_date <= end_dt)
                
                consumables_checkouts = consumables_query.limit(200).all()
                
                # Batch load inventory items to avoid N+1 queries
                item_ids = set()
                for c in consumables_checkouts:
                    if c.consumables_audit_data:
                        try:
                            if isinstance(c.consumables_audit_data, str):
                                import json
                                consumables_data = json.loads(c.consumables_audit_data)
                            elif isinstance(c.consumables_audit_data, dict):
                                consumables_data = c.consumables_audit_data
                            else:
                                continue
                            item_ids.update([int(k) for k in consumables_data.keys() if k.isdigit()])
                        except:
                            continue
                
                # Pre-load all inventory items and categories
                inventory_items_map = {}
                if item_ids:
                    items = db.query(InventoryItem).options(
                        joinedload(InventoryItem.category)
                    ).filter(InventoryItem.id.in_(list(item_ids))).all()
                    inventory_items_map = {item.id: item for item in items}
                
                for c in consumables_checkouts:
                    if not c.consumables_audit_data:
                        continue
                    
                    # Parse consumables_audit_data JSON
                    # Format: {item_id: {actual: int, limit: int, charge: float}}
                    # SQLAlchemy JSON columns return dict directly, but handle string case too
                    try:
                        if isinstance(c.consumables_audit_data, str):
                            import json
                            consumables_data = json.loads(c.consumables_audit_data)
                        elif isinstance(c.consumables_audit_data, dict):
                            consumables_data = c.consumables_audit_data
                        else:
                            continue
                        
                        for item_id_str, item_data in consumables_data.items():
                            try:
                                item_id = int(item_id_str)
                                charge = float(item_data.get("charge", 0))
                                actual_consumed = float(item_data.get("actual", 0))
                                
                                if charge <= 0:
                                    continue  # Skip free items
                                
                                consumables_count += 1
                                
                                # Get inventory item from pre-loaded map
                                inventory_item = inventory_items_map.get(item_id)
                                if not inventory_item:
                                    continue
                                
                                # Get HSN code from item or category
                                hsn_code = inventory_item.hsn_code
                                if not hsn_code and inventory_item.category:
                                    hsn_code = inventory_item.category.hsn_sac_code
                                
                                if not hsn_code:
                                    # Default HSN for goods if not specified
                                    hsn_code = "999999"  # Other goods
                                
                                # Get GST rate from item or category
                                gst_rate = float(inventory_item.gst_rate or 0)
                                if gst_rate == 0 and inventory_item.category:
                                    try:
                                        gst_rate = float(inventory_item.category.gst_tax_rate or 0)
                                        if gst_rate == 0:
                                            gst_rate = float(inventory_item.category.default_gst_rate or 0)
                                    except (AttributeError, TypeError, ValueError):
                                        gst_rate = 0
                                
                                if gst_rate == 0:
                                    gst_rate = 5.0  # Default 5% for consumables
                                
                                # Calculate taxable value and tax
                                total_value = charge
                                taxable_value = total_value / (1 + gst_rate / 100)
                                total_tax = total_value - taxable_value
                                
                                # Get unit for UQC
                                try:
                                    unit = str(inventory_item.unit or "PCS").strip()
                                except (AttributeError, TypeError):
                                    unit = "PCS"
                                
                                # Map common units to UQC codes
                                uqc_map = {
                                    "pcs": "NOS", "piece": "NOS", "pieces": "NOS",
                                    "kg": "KGS", "kgs": "KGS", "kilogram": "KGS",
                                    "liter": "LTR", "ltr": "LTR", "litre": "LTR",
                                    "box": "BOX", "boxes": "BOX",
                                    "pack": "PKT", "packet": "PKT"
                                }
                                uqc = uqc_map.get(unit.lower() if unit else "pcs", "OTH")
                                
                                # Create key for grouping
                                key = f"{hsn_code}_{gst_rate}%"
                                if key not in hsn_summary:
                                    hsn_summary[key] = {
                                        "hsn_sac_code": hsn_code,
                                        "description": inventory_item.name or "Inventory Item",
                                        "uqc": uqc,
                                        "quantity": 0,
                                        "total_value": 0.0,
                                        "taxable_value": 0.0,
                                        "integrated_tax": 0.0,
                                        "central_tax": 0.0,
                                        "state_ut_tax": 0.0,
                                        "cess_amount": 0.0,
                                        "tax_rate": gst_rate
                                    }
                                
                                # Add to summary
                                hsn_summary[key]["quantity"] += actual_consumed
                                hsn_summary[key]["total_value"] += total_value
                                hsn_summary[key]["taxable_value"] += taxable_value
                                
                                # Calculate tax breakdown (assuming intra-state)
                                tax_breakdown = calculate_tax_breakdown(taxable_value, gst_rate, False)
                                hsn_summary[key]["integrated_tax"] += tax_breakdown["igst"]
                                hsn_summary[key]["central_tax"] += tax_breakdown["cgst"]
                                hsn_summary[key]["state_ut_tax"] += tax_breakdown["sgst"]
                                
                                # Add cess if applicable
                                try:
                                    if inventory_item.category and hasattr(inventory_item.category, 'cess_percentage'):
                                        cess_percentage = float(inventory_item.category.cess_percentage or 0)
                                        if cess_percentage > 0:
                                            cess_amount = taxable_value * (cess_percentage / 100)
                                            hsn_summary[key]["cess_amount"] += cess_amount
                                except (AttributeError, TypeError, ValueError) as cess_error:
                                    # Silently skip cess calculation if there's an error
                                    pass
                                    
                            except (ValueError, KeyError, AttributeError) as e:
                                print(f"Error processing consumable item {item_id_str}: {str(e)}")
                                continue
                                
                    except (json.JSONDecodeError, TypeError, AttributeError) as e:
                        print(f"Error parsing consumables_audit_data for checkout {c.id}: {str(e)}")
                        continue
            else:
                # Column doesn't exist, skip consumables processing
                # print("HSN/SAC Summary: consumables_audit_data column not found, skipping consumables processing")
                pass
        except Exception as consumables_error:
            # Log error but don't crash the entire endpoint
            # print(f"HSN/SAC Summary: Error processing consumables - {str(consumables_error)}")
            import traceback
            traceback.print_exc()
            # Continue with the rest of the function even if consumables processing fails

        # Debug: Log summary counts
        # print(f"HSN/SAC Summary: Rooms={room_count}, Food={food_count}, Services={service_count}, Packages={package_count}, Consumables={consumables_count}")
        # print(f"HSN/SAC Summary: Total HSN/SAC codes={len(hsn_summary)}")
        
        # Round all values and convert to list
        result_data = []
        for key in sorted(hsn_summary.keys()):
            item = hsn_summary[key]
            # Round all numeric fields
            item["quantity"] = round(item["quantity"], 2)  # Keep as float for partial quantities
            item["total_value"] = round(item["total_value"], 2)
            item["taxable_value"] = round(item["taxable_value"], 2)
            item["integrated_tax"] = round(item["integrated_tax"], 2)
            item["central_tax"] = round(item["central_tax"], 2)
            item["state_ut_tax"] = round(item["state_ut_tax"], 2)
            item["cess_amount"] = round(item["cess_amount"], 2)
            item["tax_rate"] = round(item["tax_rate"], 2)
            result_data.append(item)

        # Calculate totals
        total_quantity = sum(item["quantity"] for item in result_data)
        total_value = sum(item["total_value"] for item in result_data)
        total_taxable_value = sum(item["taxable_value"] for item in result_data)
        total_igst = sum(item["integrated_tax"] for item in result_data)
        total_cgst = sum(item["central_tax"] for item in result_data)
        total_sgst = sum(item["state_ut_tax"] for item in result_data)
        total_cess = sum(item["cess_amount"] for item in result_data)

        return {
            "period": {"start_date": start_date, "end_date": end_date},
            "total_items": len(result_data),
            "summary": {
                "total_quantity": total_quantity,
                "total_value": round(total_value, 2),
                "total_taxable_value": round(total_taxable_value, 2),
                "total_integrated_tax": round(total_igst, 2),
                "total_central_tax": round(total_cgst, 2),
                "total_state_ut_tax": round(total_sgst, 2),
                "total_cess": round(total_cess, 2)
            },
            "data": result_data
        }
    except Exception as e:
        # Catch any unhandled errors and return a proper error response
        import traceback
        error_trace = traceback.format_exc()
        # print(f"HSN/SAC Summary: Unhandled error - {str(e)}")
        # print(error_trace)
        from fastapi import HTTPException
        raise HTTPException(
            status_code=500,
            detail=f"Error generating HSN/SAC Summary: {str(e)}. Please check server logs for details."
        )
    except Exception as e:
        import traceback
        print(f"Error in HSN/SAC Summary: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error generating HSN/SAC Summary: {str(e)}")


@router.get("/credit-debit-notes")
def get_credit_debit_notes(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    branch_id: Optional[int] = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """
    Credit/Debit Note Register - For cancellations and refunds
    """
    try:
        # For now, return empty as credit/debit notes need separate tracking
        # This can be enhanced with a CreditNote/DebitNote model
        return {
            "period": {"start_date": start_date, "end_date": end_date},
            "total_records": 0,
            "data": []
        }
    except Exception as e:
        import traceback
        print(f"Error in Credit/Debit Notes: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error generating Credit/Debit Notes: {str(e)}")


@router.get("/itc-register")
def get_itc_register(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    branch_id: Optional[int] = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """
    Input Tax Credit (ITC) Register - Tax paid on purchases that can be claimed
    Required for GSTR-3B Table 4
    
    Categorizes purchases into:
    - Input Goods (Standard consumables)
    - Capital Goods (Fixed assets)
    - Input Services (Services purchased)
    - Ineligible/Blocked (Cannot claim credit)
    """
    try:
        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            try:
                if len(start_date) == 10:
                    date_obj = date_type.fromisoformat(start_date)
                    start_dt = date_obj
                else:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')).date()
            except:
                start_dt = None
        if end_date:
            try:
                if len(end_date) == 10:
                    date_obj = date_type.fromisoformat(end_date)
                    end_dt = date_obj
                else:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')).date()
            except:
                end_dt = None

        # Query purchases with all relationships - Optimized with limit
        query = (db.query(PurchaseMaster).filter(PurchaseMaster.branch_id == branch_id) if branch_id is not None else db.query(PurchaseMaster)).options(
            joinedload(PurchaseMaster.vendor),
            joinedload(PurchaseMaster.details).joinedload(PurchaseDetail.item).joinedload(InventoryItem.category)
        )
        if branch_id is not None:
            query = query.filter(PurchaseMaster.branch_id == branch_id)
        if start_dt:
            query = query.filter(PurchaseMaster.purchase_date >= start_dt)
        if end_dt:
            query = query.filter(PurchaseMaster.purchase_date <= end_dt)
        
        # Limit to prevent timeout on large datasets
        purchases = query.limit(1000).all()
        
        # Debug: Log purchase count and date range
        # print(f"ITC Register: Date range - start_dt={start_dt}, end_dt={end_dt}")
        # print(f"ITC Register: Found {len(purchases)} purchases")
        if purchases:
            # print(f"ITC Register: First purchase date={purchases[0].purchase_date}, Last purchase date={purchases[-1].purchase_date}")
            pass

        # Pre-load all vendors to ensure they're available (fallback for edge cases)
        vendor_ids = list(set([p.vendor_id for p in purchases if p.vendor_id]))
        vendors_map = {}
        if vendor_ids:
            vendors = db.query(Vendor).filter(Vendor.id.in_(vendor_ids)).all()
            vendors_map = {v.id: v for v in vendors}
            # print(f"ITC Register: Loaded {len(vendors)} vendors")

        # Categorize ITC records
        input_goods = []      # Standard consumables (Eligible)
        capital_goods = []    # Fixed assets (Eligible, tracked separately)
        input_services = []   # Services purchased (Eligible)
        ineligible = []       # Blocked credits (Section 17(5))

        for p in purchases:
            # Get vendor - try relationship first, then fallback to map, then direct query
            vendor = None
            # Try 1: Check if vendor is loaded via relationship
            if hasattr(p, 'vendor') and p.vendor is not None:
                vendor = p.vendor
            # Try 2: Check vendors_map
            elif p.vendor_id and p.vendor_id in vendors_map:
                vendor = vendors_map[p.vendor_id]
            # Try 3: Direct query as last resort
            elif p.vendor_id:
                vendor = db.query(Vendor).filter(Vendor.id == p.vendor_id).first()
                if vendor:
                    vendors_map[p.vendor_id] = vendor  # Cache it
            
            # Extract vendor details with proper fallbacks - ensure we always have values
            if vendor:
                vendor_gstin = str(vendor.gst_number) if vendor.gst_number else ""
                # Try multiple name fields in order of preference (handle None and empty strings)
                vendor_name = (
                    (vendor.legal_name and vendor.legal_name.strip()) or
                    (vendor.name and vendor.name.strip()) or
                    (getattr(vendor, 'trade_name', None) and getattr(vendor, 'trade_name', None).strip()) or
                    (getattr(vendor, 'company_name', None) and getattr(vendor, 'company_name', None).strip()) or
                    "Unknown Vendor"
                )
                vendor_state = (vendor.billing_state and vendor.billing_state.strip()) or (getattr(vendor, 'state', None) and getattr(vendor, 'state', None).strip()) or None
                
                # Debug: Verify vendor details
                # print(f"ITC Register: Purchase {p.id} - Vendor loaded: {vendor_name}, GST: {vendor_gstin}")
            else:
                vendor_gstin = ""
                vendor_name = "Unknown Vendor"
                vendor_state = None
                # print(f"ITC Register: WARNING - Purchase {p.id} has no vendor! vendor_id={p.vendor_id}")
            place_of_supply = f"{RESORT_STATE_CODE}-{STATE_CODES.get(RESORT_STATE_CODE, 'Unknown')}"
            if vendor_state:
                # Try to match vendor state to state code
                for code, state_name in STATE_CODES.items():
                    if vendor_state.lower() in state_name.lower() or state_name.lower() in vendor_state.lower():
                        place_of_supply = f"{code}-{state_name}"
                        break
            
            invoice_number = p.invoice_number or p.purchase_number or f"PO-{p.id}"
            invoice_date = p.invoice_date if p.invoice_date else p.purchase_date
            invoice_value = float(p.total_amount or 0)
            
            # Debug: Log invoice details
            # print(f"ITC Register: Processing purchase {p.id}, Invoice: {invoice_number}, Date: {invoice_date}, Vendor: {vendor_name}, GST: {vendor_gstin}")
            
            for detail in p.details:
                item = detail.item
                category = item.category if item else None
                
                # Determine ITC eligibility and type
                itc_eligibility = "Eligible"
                itc_type = "Input Goods"  # Default
                
                if category:
                    # Check ITC eligibility from category
                    if category.itc_eligibility and "Ineligible" in category.itc_eligibility:
                        itc_eligibility = "Ineligible"
                    elif category.itc_eligibility and "Blocked" in category.itc_eligibility:
                        itc_eligibility = "Ineligible"
                    
                    # Determine type based on category properties
                    if category.is_capital_good or category.is_asset_fixed:
                        itc_type = "Capital Goods"
                    elif category.classification and category.classification.lower() == "services":
                        itc_type = "Input Services"
                    else:
                        itc_type = "Input Goods"
                
                # Calculate taxable value (excluding tax)
                taxable_value = float(detail.total_amount or 0) - float(detail.cgst_amount or 0) - float(detail.sgst_amount or 0) - float(detail.igst_amount or 0)
                igst = float(detail.igst_amount or 0)
                cgst = float(detail.cgst_amount or 0)
                sgst = float(detail.sgst_amount or 0)
                total_tax = igst + cgst + sgst
                tax_rate = float(detail.gst_rate or 0)
                hsn_code = detail.hsn_code or (item.hsn_code if item else None)
                
                itc_record = {
                    "vendor_gstin": vendor_gstin or "",
                    "supplier_name": vendor_name,
                    "invoice_number": invoice_number or "N/A",
                    "invoice_date": invoice_date.isoformat() + "Z" if invoice_date else (p.purchase_date.isoformat() + "Z" if p.purchase_date else None),
                    "invoice_value": round(invoice_value, 2),
                    "place_of_supply": place_of_supply,
                    "hsn_code": hsn_code or "",
                    "item_name": item.name if item else "Unknown Item",
                    "category_name": category.name if category else "Uncategorized",
                    "tax_rate": round(tax_rate, 2),
                    "taxable_value": round(taxable_value, 2),
                    "igst": round(igst, 2),
                    "cgst": round(cgst, 2),
                    "sgst": round(sgst, 2),
                    "total_tax": round(total_tax, 2),
                    "itc_type": itc_type,
                    "itc_eligibility": itc_eligibility,
                    "gstr2b_matched": False,  # For future GSTR-2B reconciliation
                    "gstr2b_notes": ""  # For reconciliation notes
                }

                # Debug: Log the record being created
                # print(f"ITC Register: Creating record - Vendor: {vendor_name} ({vendor_gstin}), Invoice: {invoice_number}, Item: {item.name if item else 'None'}, Tax: {total_tax}, Eligibility: {itc_eligibility}, Type: {itc_type}")
                
                # Categorize based on eligibility and type
                if itc_eligibility == "Ineligible":
                    ineligible.append(itc_record)
                    # print(f"ITC Register: [OK] Added to ineligible - {vendor_name}, Invoice: {invoice_number}, Tax: {total_tax}")
                elif itc_type == "Capital Goods":
                    capital_goods.append(itc_record)
                    # print(f"ITC Register: [OK] Added to capital_goods - {vendor_name}, Invoice: {invoice_number}, Tax: {total_tax}")
                elif itc_type == "Input Services":
                    input_services.append(itc_record)
                    # print(f"ITC Register: [OK] Added to input_services - {vendor_name}, Invoice: {invoice_number}, Tax: {total_tax}")
                else:  # Input Goods
                    input_goods.append(itc_record)
                    # print(f"ITC Register: [OK] Added to input_goods - {vendor_name}, Invoice: {invoice_number}, Tax: {total_tax}")

        # Calculate totals
        def calculate_totals(records):
            return {
                "total_records": len(records),
                "total_taxable_value": sum([r["taxable_value"] for r in records]),
                "total_igst": sum([r["igst"] for r in records]),
                "total_cgst": sum([r["cgst"] for r in records]),
                "total_sgst": sum([r["sgst"] for r in records]),
                "total_tax": sum([r["total_tax"] for r in records])
            }

        eligible_total = calculate_totals(input_goods + capital_goods + input_services)
        ineligible_total = calculate_totals(ineligible)
        
        # Debug: Log totals and sample data
        # print(f"ITC Register: Input Goods={len(input_goods)}, Capital Goods={len(capital_goods)}, Input Services={len(input_services)}, Ineligible={len(ineligible)}")
        # print(f"ITC Register: Total Eligible ITC={eligible_total['total_tax']}, Total Ineligible ITC={ineligible_total['total_tax']}")
        # print(f"ITC Register: All Eligible records={len(input_goods + capital_goods + input_services)}")
        if input_goods:
            # print(f"ITC Register: Sample Input Goods record: Vendor={input_goods[0].get('supplier_name')}, GST={input_goods[0].get('vendor_gstin')}, Invoice={input_goods[0].get('invoice_number')}")
            pass
        if input_goods + capital_goods + input_services:
            all_eligible_sample = (input_goods + capital_goods + input_services)[0]
            # print(f"ITC Register: Sample All Eligible record: Vendor={all_eligible_sample.get('supplier_name')}, GST={all_eligible_sample.get('vendor_gstin')}, Invoice={all_eligible_sample.get('invoice_number')}")
            pass

        return {
            "period": {"start_date": start_date, "end_date": end_date},
            "summary": {
                "total_eligible_itc": eligible_total["total_tax"],
                "total_ineligible_itc": ineligible_total["total_tax"],
                "net_claimable_itc": eligible_total["total_tax"],
                "total_purchases": len(purchases),
                "total_invoice_value": sum([float(p.total_amount or 0) for p in purchases])
            },
            "input_goods": {
                "description": "Standard Input Goods (Eligible ITC)",
                **calculate_totals(input_goods),
                "data": input_goods
            },
            "capital_goods": {
                "description": "Capital Goods / Fixed Assets (Eligible ITC)",
                **calculate_totals(capital_goods),
                "data": capital_goods
            },
            "input_services": {
                "description": "Input Services (Eligible ITC)",
                **calculate_totals(input_services),
                "data": input_services
            },
            "ineligible": {
                "description": "Ineligible / Blocked Credits (Section 17(5))",
                **calculate_totals(ineligible),
                "data": ineligible
            },
            "all_eligible": {
                "description": "All Eligible ITC (Combined)",
                **eligible_total,
                "data": input_goods + capital_goods + input_services
            }
        }
    except Exception as e:
        import traceback
        # print(f"Error in ITC Register: {str(e)}\n{traceback.format_exc()}")
        tb = traceback.format_exc()
        # traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating ITC Register: {str(e)}")


@router.post("/itc-register/reconcile-gstr2b")
async def reconcile_gstr2b(
    file: UploadFile = File(...),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    branch_id: Optional[int] = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """
    GSTR-2B Reconciliation - Upload GSTR-2B Excel file and match with ITC Register
    Matches invoice numbers from GSTR-2B with your purchase invoices
    Returns mismatches and reconciliation status
    """
    if not PANDAS_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="GSTR-2B reconciliation requires pandas and openpyxl. Please install: pip install pandas openpyxl"
        )
    
    try:
        # Validate file type
        if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            raise HTTPException(status_code=400, detail="File must be Excel (.xlsx, .xls) or CSV (.csv)")
        
        # Read file content
        contents = await file.read()
        
        # Parse Excel/CSV
        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(io.BytesIO(contents))
            else:
                df = pd.read_excel(io.BytesIO(contents))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")
        
        # Extract invoice numbers from GSTR-2B
        # GSTR-2B typically has columns: Invoice Number, Invoice Date, GSTIN, etc.
        # Try common column names
        invoice_col = None
        for col in df.columns:
            col_lower = str(col).lower()
            if 'invoice' in col_lower and 'number' in col_lower:
                invoice_col = col
                break
            elif 'invoice' in col_lower and 'no' in col_lower:
                invoice_col = col
                break
            elif 'inv' in col_lower:
                invoice_col = col
                break
        
        if invoice_col is None:
            # Try first column as fallback
            invoice_col = df.columns[0]
        
        gstr2b_invoices = set()
        for idx, row in df.iterrows():
            invoice_num = str(row[invoice_col]).strip() if pd.notna(row[invoice_col]) else None
            if invoice_num and invoice_num.lower() not in ['nan', 'none', '']:
                gstr2b_invoices.add(invoice_num)
        
        # Parse dates for ITC register query
        start_dt = None
        end_dt = None
        if start_date:
            try:
                if len(start_date) == 10:
                    date_obj = date_type.fromisoformat(start_date)
                    start_dt = date_obj
                else:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')).date()
            except:
                start_dt = None
        if end_date:
            try:
                if len(end_date) == 10:
                    date_obj = date_type.fromisoformat(end_date)
                    end_dt = date_obj
                else:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')).date()
            except:
                end_dt = None
        
        # Query purchases
        query = (db.query(PurchaseMaster).filter(PurchaseMaster.branch_id == branch_id) if branch_id is not None else db.query(PurchaseMaster)).options(
            joinedload(PurchaseMaster.vendor),
            joinedload(PurchaseMaster.details).joinedload(PurchaseDetail.item).joinedload(InventoryItem.category)
        )
        if branch_id is not None:
            query = query.filter(PurchaseMaster.branch_id == branch_id)
        if start_dt:
            query = query.filter(PurchaseMaster.purchase_date >= start_dt)
        if end_dt:
            query = query.filter(PurchaseMaster.purchase_date <= end_dt)
        
        purchases = query.limit(500).all()
        
        # Build invoice mapping from purchases
        purchase_invoices = {}
        for p in purchases:
            # Ensure vendor is loaded
            vendor = p.vendor
            if not vendor and hasattr(p, 'vendor_id') and p.vendor_id:
                vendor = db.query(Vendor).filter(Vendor.id == p.vendor_id).first()
            
            invoice_number = p.invoice_number or p.purchase_number
            if invoice_number:
                purchase_invoices[invoice_number.strip()] = {
                    "purchase_id": p.id,
                    "invoice_number": invoice_number,
                    "invoice_date": p.invoice_date.isoformat() + "Z" if p.invoice_date else p.purchase_date.isoformat() + "Z",
                    "vendor_name": (vendor.legal_name or vendor.name or getattr(vendor, 'trade_name', None)) if vendor else "Unknown Vendor",
                    "vendor_gstin": vendor.gst_number if vendor else None,
                    "total_amount": float(p.total_amount or 0)
                }
        
        # Match invoices
        matched = []
        unmatched_in_gstr2b = []  # In GSTR-2B but not in our system
        unmatched_in_system = []  # In our system but not in GSTR-2B
        
        # Check GSTR-2B invoices against our system
        for gstr2b_inv in gstr2b_invoices:
            if gstr2b_inv in purchase_invoices:
                matched.append({
                    "invoice_number": gstr2b_inv,
                    **purchase_invoices[gstr2b_inv],
                    "status": "matched"
                })
            else:
                unmatched_in_gstr2b.append({
                    "invoice_number": gstr2b_inv,
                    "status": "not_found_in_system"
                })
        
        # Check our invoices against GSTR-2B
        for inv_num, inv_data in purchase_invoices.items():
            if inv_num not in gstr2b_invoices:
                unmatched_in_system.append({
                    **inv_data,
                    "status": "not_found_in_gstr2b"
                })
        
        return {
            "file_name": file.filename,
            "total_gstr2b_invoices": len(gstr2b_invoices),
            "total_system_invoices": len(purchase_invoices),
            "matched_count": len(matched),
            "unmatched_in_gstr2b_count": len(unmatched_in_gstr2b),
            "unmatched_in_system_count": len(unmatched_in_system),
            "match_percentage": round((len(matched) / len(purchase_invoices) * 100) if purchase_invoices else 0, 2),
            "matched": matched,
            "unmatched_in_gstr2b": unmatched_in_gstr2b[:100],  # Limit to 100 for response size
            "unmatched_in_system": unmatched_in_system[:100],  # Limit to 100 for response size
            "summary": {
                "total_eligible_itc": sum([float(p.total_amount or 0) * 0.18 for p in purchases]),  # Approximate
                "matched_itc": len(matched) * 1000,  # Placeholder calculation
                "unmatched_itc": len(unmatched_in_system) * 1000  # Placeholder calculation
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error in GSTR-2B Reconciliation: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error reconciling GSTR-2B: {str(e)}")


@router.get("/rcm-register")
def get_rcm_register(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    branch_id: Optional[int] = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """
    Reverse Charge Mechanism (RCM) Register - Comprehensive RCM transactions
    Includes both Purchases and Expenses marked as RCM applicable
    
    This report feeds into GSTR-3B (Table 3.1.d)
    
    Columns:
    - RCM Invoice No: Self-invoice number (SLF-YYYY-XXX) or purchase invoice
    - RCM Date: Date when liability arises (payment date or 60 days from invoice)
    - Supplier Name: Vendor name
    - Nature of Supply: GTA, Legal Services, Import of Service, Security Services
    - Original Bill No: Original bill/receipt number from vendor
    - Taxable Value: Base amount (vendor gets this, no tax)
    - Tax Rate: GST rate (5% for GTA, 18% for Legal, etc.)
    - Tax Liability: Calculated tax amount
    - ITC Eligibility: Eligible / Ineligible
    """
    try:
        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            try:
                if len(start_date) == 10:
                    start_dt = date_type.fromisoformat(start_date)
                else:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')).date()
            except:
                start_dt = None
        if end_date:
            try:
                if len(end_date) == 10:
                    end_dt = date_type.fromisoformat(end_date)
                else:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')).date()
            except:
                end_dt = None

        rcm_data = []
        
        # 1. Query Expenses with RCM applicable
        expense_query = (db.query(Expense).filter(Expense.branch_id == branch_id) if branch_id is not None else db.query(Expense)).options(
            joinedload(Expense.vendor),
            joinedload(Expense.employee)
        ).filter(Expense.rcm_applicable == True)
        
        if branch_id is not None:
            expense_query = expense_query.filter(Expense.branch_id == branch_id)
        
        if start_dt:
            expense_query = expense_query.filter(Expense.date >= start_dt)
        if end_dt:
            expense_query = expense_query.filter(Expense.date <= end_dt)
        
        expenses = expense_query.limit(500).all()
        
        for exp in expenses:
            # Determine if inter-state (check vendor state vs resort state)
            is_interstate = False
            vendor_state_code = None
            if exp.vendor and exp.vendor.billing_state:
                # Extract state code from vendor state name or GSTIN
                vendor_gstin = exp.vendor.gst_number
                if vendor_gstin and len(vendor_gstin) >= 2:
                    vendor_state_code = vendor_gstin[:2]
                    is_interstate = vendor_state_code != RESORT_STATE_CODE
            
            # Calculate tax breakdown
            taxable_value = float(exp.amount or 0)
            tax_rate = float(exp.rcm_tax_rate or 18.0)  # Default 18%
            tax_amount = taxable_value * (tax_rate / 100)
            
            if is_interstate:
                igst = tax_amount
                cgst = 0.0
                sgst = 0.0
            else:
                igst = 0.0
                cgst = tax_amount / 2
                sgst = tax_amount / 2
            
            # Get vendor details
            vendor_name = "Unknown"
            vendor_gstin = None
            if exp.vendor:
                vendor_name = (exp.vendor.legal_name and exp.vendor.legal_name.strip()) or \
                             (exp.vendor.name and exp.vendor.name.strip()) or \
                             (getattr(exp.vendor, 'trade_name', None) and getattr(exp.vendor, 'trade_name', None).strip()) or \
                             (getattr(exp.vendor, 'company_name', None) and getattr(exp.vendor, 'company_name', None).strip()) or \
                             "Unknown Vendor"
                vendor_gstin = exp.vendor.gst_number or None
            
            # RCM Date: Use rcm_liability_date if set, otherwise use expense date
            rcm_date = exp.rcm_liability_date if exp.rcm_liability_date else exp.date
            
            rcm_data.append({
                "rcm_invoice_no": exp.self_invoice_number or f"EXP-{exp.id}",  # Self-invoice or expense ID
                "rcm_date": rcm_date.isoformat() + "Z" if rcm_date else exp.date.isoformat() + "Z",
                "supplier_name": vendor_name,
                "supplier_gstin": vendor_gstin,
                "nature_of_supply": exp.nature_of_supply or "Other",
                "original_bill_no": exp.original_bill_no or None,
                "taxable_value": round(taxable_value, 2),
                "tax_rate": round(tax_rate, 2),
                "tax_liability": round(tax_amount, 2),
                "igst": round(igst, 2),
                "cgst": round(cgst, 2),
                "sgst": round(sgst, 2),
                "itc_eligibility": "Eligible" if exp.itc_eligible else "Ineligible",
                "source_type": "Expense",
                "source_id": exp.id,
                "place_of_supply": get_place_of_supply(vendor_gstin) if vendor_gstin else "Unknown"
            })
        
        # 2. Query Purchases where RCM is applicable - Optimized with eager loading
        purchase_query = (db.query(PurchaseMaster).filter(PurchaseMaster.branch_id == branch_id) if branch_id is not None else db.query(PurchaseMaster)).options(
            joinedload(PurchaseMaster.vendor),
            joinedload(PurchaseMaster.details).joinedload(PurchaseDetail.item).joinedload(InventoryItem.category)
        ).join(Vendor).filter(Vendor.rcm_applicable == True)
        if branch_id is not None:
            purchase_query = purchase_query.filter(PurchaseMaster.branch_id == branch_id)
        
        if start_dt:
            purchase_query = purchase_query.filter(PurchaseMaster.purchase_date >= start_dt)
        if end_dt:
            purchase_query = purchase_query.filter(PurchaseMaster.purchase_date <= end_dt)
        
        purchases = purchase_query.limit(500).all()
        
        for p in purchases:
            # Ensure vendor is loaded
            vendor = p.vendor
            if not vendor and p.vendor_id:
                vendor = db.query(Vendor).filter(Vendor.id == p.vendor_id).first()
            
            # Determine if inter-state
            is_interstate = False
            vendor_state_code = None
            if vendor and vendor.gst_number:
                vendor_state_code = vendor.gst_number[:2] if len(vendor.gst_number) >= 2 else None
                is_interstate = vendor_state_code and vendor_state_code != RESORT_STATE_CODE
            
            vendor_name = (vendor.legal_name and vendor.legal_name.strip()) or \
                         (vendor.name and vendor.name.strip()) or \
                         (getattr(vendor, 'trade_name', None) and getattr(vendor, 'trade_name', None).strip()) or \
                         (getattr(vendor, 'company_name', None) and getattr(vendor, 'company_name', None).strip()) or \
                         "Unknown Vendor" if vendor else "Unknown"
            vendor_gstin = vendor.gst_number if vendor else None
            
            for detail in p.details:
                # Calculate taxable value (excluding tax)
                taxable_value = float(detail.total_amount or 0) - float(detail.cgst_amount or 0) - float(detail.sgst_amount or 0) - float(detail.igst_amount or 0)
                
                # If taxable value is 0, use total_amount as base
                if taxable_value <= 0:
                    taxable_value = float(detail.total_amount or 0)
                
                # Calculate tax rate from existing tax amounts
                existing_igst = float(detail.igst_amount or 0)
                existing_cgst = float(detail.cgst_amount or 0)
                existing_sgst = float(detail.sgst_amount or 0)
                total_existing_tax = existing_igst + existing_cgst + existing_sgst
                
                if total_existing_tax > 0 and taxable_value > 0:
                    tax_rate = (total_existing_tax / taxable_value) * 100
                else:
                    # Default tax rate based on nature (assume 18% for purchases)
                    tax_rate = 18.0
                
                tax_liability = total_existing_tax if total_existing_tax > 0 else (taxable_value * (tax_rate / 100))
                
                # Determine ITC eligibility from category
                itc_eligible = True
                if detail.item and detail.item.category:
                    category = detail.item.category
                    itc_eligible = getattr(category, 'itc_eligibility', True) if hasattr(category, 'itc_eligibility') else True
                
                # RCM Date: Use purchase date or invoice date
                rcm_date = p.invoice_date if p.invoice_date else p.purchase_date
                
                rcm_data.append({
                    "rcm_invoice_no": p.invoice_number or p.purchase_number or f"PUR-{p.id}",
                    "rcm_date": rcm_date.isoformat() + "Z" if rcm_date else p.purchase_date.isoformat() + "Z",
                    "supplier_name": vendor_name,
                    "supplier_gstin": vendor_gstin,
                    "nature_of_supply": "GTA" if "transport" in (detail.item.name or "").lower() else "Other",  # Default, can be enhanced
                    "original_bill_no": p.invoice_number or p.purchase_number,
                    "taxable_value": round(taxable_value, 2),
                    "tax_rate": round(tax_rate, 2),
                    "tax_liability": round(tax_liability, 2),
                    "igst": round(existing_igst, 2),
                    "cgst": round(existing_cgst, 2),
                    "sgst": round(existing_sgst, 2),
                    "itc_eligibility": "Eligible" if itc_eligible else "Ineligible",
                    "source_type": "Purchase",
                    "source_id": p.id,
                    "place_of_supply": get_place_of_supply(vendor_gstin) if vendor_gstin else "Unknown",
                    "hsn_code": detail.hsn_code or (detail.item.hsn_code if detail.item else None)
                })

        # Sort by RCM date descending
        rcm_data.sort(key=lambda x: x.get("rcm_date", ""), reverse=True)
        
        # Calculate summary totals
        total_tax_liability = sum([r["tax_liability"] for r in rcm_data])
        total_igst = sum([r["igst"] for r in rcm_data])
        total_cgst = sum([r["cgst"] for r in rcm_data])
        total_sgst = sum([r["sgst"] for r in rcm_data])
        total_taxable_value = sum([r["taxable_value"] for r in rcm_data])
        
        return {
            "period": {"start_date": start_date, "end_date": end_date},
            "summary": {
                "total_records": len(rcm_data),
                "total_taxable_value": round(total_taxable_value, 2),
                "total_tax_liability": round(total_tax_liability, 2),
                "total_igst": round(total_igst, 2),
                "total_cgst": round(total_cgst, 2),
                "total_sgst": round(total_sgst, 2)
            },
            "data": rcm_data
        }
    except Exception as e:
        import traceback
        print(f"Error in RCM Register: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error generating RCM Register: {str(e)}")


@router.get("/advance-receipt")
def get_advance_receipt_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    branch_id: Optional[int] = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """
    Advance Receipt Register - Tax liability on money received before invoice is raised
    Required for GSTR-1
    
    Fields:
    - Place of Supply: State of the guest
    - Rate (%): Tax Slab (e.g., 18% for advance on luxury room)
    - Gross Advance Received: Total money received
    - Tax Amounts: IGST, CGST, SGST, Cess calculated on the advance
    """
    try:
        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            try:
                if len(start_date) == 10:
                    date_obj = date_type.fromisoformat(start_date)
                    start_dt = date_obj
                else:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00')).date()
            except:
                start_dt = None
        if end_dt:
            try:
                if len(end_date) == 10:
                    date_obj = date_type.fromisoformat(end_date)
                    end_dt = date_obj
                else:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')).date()
            except:
                end_dt = None
        
        # Query bookings with advance deposits (unadjusted - invoice not raised yet)
        query = (db.query(Booking).filter(Booking.branch_id == branch_id) if branch_id is not None else db.query(Booking)).filter(Booking.advance_deposit > 0)
        if branch_id is not None:
            query = query.filter(Booking.branch_id == branch_id)
        if start_dt:
            query = query.filter(Booking.check_in >= start_dt)
        if end_dt:
            query = query.filter(Booking.check_in <= end_dt)
        
        # Also query package bookings
        pkg_query = (db.query(PackageBooking).filter(PackageBooking.branch_id == branch_id) if branch_id is not None else db.query(PackageBooking)).filter(PackageBooking.advance_deposit > 0)
        if branch_id is not None:
            pkg_query = pkg_query.filter(PackageBooking.branch_id == branch_id)
        if start_dt:
            pkg_query = pkg_query.filter(PackageBooking.check_in >= start_dt)
        if end_dt:
            pkg_query = pkg_query.filter(PackageBooking.check_in <= end_dt)

        bookings = query.limit(500).all()
        package_bookings = pkg_query.limit(500).all()

        advance_data = []
        advance_by_state = {}  # Group by Place of Supply and Rate
        
        # Regular bookings
        for b in bookings:
            checkout = b.checkout if hasattr(b, 'checkout') else None
            invoice_raised = checkout is not None
            
            # Only include unadjusted advances (invoice not raised)
            if not invoice_raised:
                advance_amount = float(b.advance_deposit or 0)
                if advance_amount > 0:
                    # Determine tax rate based on room type/amount
                    # For advance, typically use 18% for luxury rooms, 12% for standard
                    # Use booking total_amount as proxy for room type
                    tax_rate = get_room_tax_rate(float(b.total_amount or 0))
                    
                    # Calculate taxable value and tax
                    taxable_value = advance_amount / (1 + tax_rate / 100)
                    total_tax = advance_amount - taxable_value
                    
                    # Assume intra-state (can be enhanced with guest state)
                    is_interstate = False
                    tax_breakdown = calculate_tax_breakdown(taxable_value, tax_rate, is_interstate)
                    
                    # Place of Supply (default to resort state, can be enhanced)
                    place_of_supply = f"{RESORT_STATE_CODE}-{STATE_CODES.get(RESORT_STATE_CODE, 'Unknown')}"
                    
                    # Group by Place of Supply and Rate for aggregated reporting
                    key = f"{place_of_supply}_{tax_rate}%"
                    if key not in advance_by_state:
                        advance_by_state[key] = {
                            "place_of_supply": place_of_supply,
                            "rate": tax_rate,
                            "gross_advance_received": 0.0,
                            "taxable_value": 0.0,
                            "igst": 0.0,
                            "cgst": 0.0,
                            "sgst": 0.0,
                            "cess": 0.0,
                            "count": 0
                        }
                    
                    advance_by_state[key]["gross_advance_received"] += advance_amount
                    advance_by_state[key]["taxable_value"] += taxable_value
                    advance_by_state[key]["igst"] += tax_breakdown["igst"]
                    advance_by_state[key]["cgst"] += tax_breakdown["cgst"]
                    advance_by_state[key]["sgst"] += tax_breakdown["sgst"]
                    advance_by_state[key]["count"] += 1
                    
                    advance_data.append({
                        "receipt_date": b.check_in.isoformat() + "Z" if b.check_in else None,
                        "booking_id": b.id,
                        "booking_type": "Regular",
                        "guest_name": b.guest_name,
                        "place_of_supply": place_of_supply,
                        "rate": tax_rate,
                        "gross_advance_received": round(advance_amount, 2),
                        "taxable_value": round(taxable_value, 2),
                        "igst": round(tax_breakdown["igst"], 2),
                        "cgst": round(tax_breakdown["cgst"], 2),
                        "sgst": round(tax_breakdown["sgst"], 2),
                        "cess": 0.0,
                        "invoice_raised": False
                    })

        # Package bookings
        for pb in package_bookings:
            checkout = pb.checkout if hasattr(pb, 'checkout') else None
            invoice_raised = checkout is not None
            
            if not invoice_raised:
                advance_amount = float(pb.advance_deposit or 0)
                if advance_amount > 0:
                    # Package advances typically 18% (luxury)
                    tax_rate = 18.0
                    taxable_value = advance_amount / (1 + tax_rate / 100)
                    total_tax = advance_amount - taxable_value
                    
                    is_interstate = False
                    tax_breakdown = calculate_tax_breakdown(taxable_value, tax_rate, is_interstate)
                    place_of_supply = f"{RESORT_STATE_CODE}-{STATE_CODES.get(RESORT_STATE_CODE, 'Unknown')}"
                    
                    key = f"{place_of_supply}_{tax_rate}%"
                    if key not in advance_by_state:
                        advance_by_state[key] = {
                            "place_of_supply": place_of_supply,
                            "rate": tax_rate,
                            "gross_advance_received": 0.0,
                            "taxable_value": 0.0,
                            "igst": 0.0,
                            "cgst": 0.0,
                            "sgst": 0.0,
                            "cess": 0.0,
                            "count": 0
                        }
                    
                    advance_by_state[key]["gross_advance_received"] += advance_amount
                    advance_by_state[key]["taxable_value"] += taxable_value
                    advance_by_state[key]["igst"] += tax_breakdown["igst"]
                    advance_by_state[key]["cgst"] += tax_breakdown["cgst"]
                    advance_by_state[key]["sgst"] += tax_breakdown["sgst"]
                    advance_by_state[key]["count"] += 1
                    
                    advance_data.append({
                        "receipt_date": pb.check_in.isoformat() + "Z" if pb.check_in else None,
                        "booking_id": pb.id,
                        "booking_type": "Package",
                        "guest_name": pb.guest_name,
                        "place_of_supply": place_of_supply,
                        "rate": tax_rate,
                        "gross_advance_received": round(advance_amount, 2),
                        "taxable_value": round(taxable_value, 2),
                        "igst": round(tax_breakdown["igst"], 2),
                        "cgst": round(tax_breakdown["cgst"], 2),
                        "sgst": round(tax_breakdown["sgst"], 2),
                        "cess": 0.0,
                        "invoice_raised": False
                    })

        # Round aggregated values
        for key in advance_by_state:
            for field in ["gross_advance_received", "taxable_value", "igst", "cgst", "sgst"]:
                advance_by_state[key][field] = round(advance_by_state[key][field], 2)

        total_advance = sum([a["gross_advance_received"] for a in advance_data])
        total_tax_liability = sum([a["igst"] + a["cgst"] + a["sgst"] for a in advance_data])

        return {
            "period": {"start_date": start_date, "end_date": end_date},
            "total_advance_received": round(total_advance, 2),
            "total_tax_liability": round(total_tax_liability, 2),
            "total_records": len(advance_data),
            "aggregated_by_state": list(advance_by_state.values()),  # For GSTR-1 filing
            "data": advance_data  # Detailed records
        }
    except Exception as e:
        import traceback
        print(f"Error in Advance Receipt Report: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error generating Advance Receipt Report: {str(e)}")


@router.get("/room-tariff-slab")
def get_room_tariff_slab_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    branch_id: Optional[int] = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """
    Room Tariff Slab Report - Verify correct tax rate applied
    Rooms ≤ Rs.4,999: 5% GST
    Rooms Rs.5,000 - Rs.7,499: 12% GST
    Rooms ≥ Rs.7,500: 18% GST
    """
    try:
        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            try:
                if len(start_date) == 10:
                    date_obj = date_type.fromisoformat(start_date)
                    start_dt = datetime.combine(date_obj, datetime.min.time())
                else:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except:
                start_dt = None
        if end_date:
            try:
                if len(end_date) == 10:
                    date_obj = date_type.fromisoformat(end_date)
                    end_dt = datetime.combine(date_obj, datetime.max.time())
                else:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except:
                end_dt = None

        query = (db.query(Checkout).filter(Checkout.branch_id == branch_id) if branch_id is not None else db.query(Checkout)).filter(Checkout.room_total > 0)
        if branch_id is not None:
            query = query.filter(Checkout.branch_id == branch_id)
        if start_dt:
            query = query.filter(Checkout.checkout_date >= start_dt)
        if end_dt:
            query = query.filter(Checkout.checkout_date <= end_dt)
        
        # Order by checkout date for consistency
        query = query.order_by(Checkout.checkout_date.desc())
        
        # Get all checkouts - no limit for accurate reporting
        checkouts = query.all()
        
        # Debug: Log checkout count and date range
        # print(f"Room Tariff Slab: Date range - start_dt={start_dt}, end_dt={end_dt}")
        # print(f"Room Tariff Slab: Found {len(checkouts)} checkouts with room_total > 0")
        if checkouts:
            # print(f"Room Tariff Slab: First checkout date={checkouts[0].checkout_date}, Last checkout date={checkouts[-1].checkout_date}")
            pass

        slab_5 = []   # <= Rs.4,999 (5% GST)
        slab_12 = []  # Rs.5,000 - Rs.7,499 (12% GST)
        slab_18 = []  # >= Rs.7,500 (18% GST)

        for c in checkouts:
            room_total = float(c.room_total or 0)
            expected_rate = get_room_tax_rate(room_total)
            
            invoice_data = {
                "invoice_date": c.checkout_date.isoformat() + "Z" if c.checkout_date else None,
                "invoice_number": c.invoice_number or f"INV-{c.id:06d}",
                "guest_name": c.guest_name or "Unknown Guest",
                "room_total": round(room_total, 2),
                "expected_tax_rate": expected_rate,
                "tax_applied": round(float(c.tax_amount or 0), 2),
                "tax_rate_applied": round((float(c.tax_amount or 0) / room_total * 100) if room_total > 0 else 0, 2)
            }
            
            # Debug: Log room data
            # print(f"Room Tariff Slab: Checkout {c.id}, Date: {c.checkout_date}, Room Total: Rs.{room_total}, Tax Rate: {expected_rate}%, Slab: {'5%' if expected_rate == 5.0 else '12%' if expected_rate == 12.0 else '18%'}")

            if expected_rate == 5.0:
                slab_5.append(invoice_data)
            elif expected_rate == 12.0:
                slab_12.append(invoice_data)
            else:
                slab_18.append(invoice_data)
        
        # Debug: Log slab counts
        # print(f"Room Tariff Slab: Slab 5% = {len(slab_5)}, Slab 12% = {len(slab_12)}, Slab 18% = {len(slab_18)}")

        return {
            "period": {"start_date": start_date, "end_date": end_date},
            "slab_5_percent": {
                "description": "Rooms <= Rs.4,999 (5% GST)",
                "total_invoices": len(slab_5),
                "total_revenue": round(sum([s["room_total"] for s in slab_5]), 2),
                "data": slab_5
            },
            "slab_12_percent": {
                "description": "Rooms Rs.5,000 - Rs.7,499 (12% GST)",
                "total_invoices": len(slab_12),
                "total_revenue": round(sum([s["room_total"] for s in slab_12]), 2),
                "data": slab_12
            },
            "slab_18_percent": {
                "description": "Rooms >= Rs.7,500 (18% GST)",
                "total_invoices": len(slab_18),
                "total_revenue": round(sum([s["room_total"] for s in slab_18]), 2),
                "data": slab_18
            }
        }
    except Exception as e:
        import traceback
        # print(f"Error in Room Tariff Slab Report: {str(e)}\n{traceback.format_exc()}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating Room Tariff Slab Report: {repr(e)}")


@router.get("/master-summary")
def get_master_gst_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    branch_id: int = Depends(get_branch_id),
    current_user: User = Depends(get_current_user)
):
    """
    Master GST Summary - Executive dashboard view
    High-level dashboard for owner/accountant to see total liability
    
    Includes:
    - Total Outward Supplies (Sales): Total value of all bills generated
    - Total Taxable Value: Value before tax
    - Total Output Tax: (IGST + CGST + SGST) collected from guests
    - Total Input Tax Credit (ITC): Tax paid to vendors
    - Net GST Payable: (Total Output Tax - Total ITC)
    - Total RCM Liability: Amount for unregistered vendor services
    """
    try:
        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            try:
                if len(start_date) == 10:
                    date_obj = date_type.fromisoformat(start_date)
                    start_dt = datetime.combine(date_obj, datetime.min.time())
                else:
                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except:
                start_dt = None
        if end_date:
            try:
                if len(end_date) == 10:
                    date_obj = date_type.fromisoformat(end_date)
                    end_dt = datetime.combine(date_obj, datetime.max.time())
                else:
                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except:
                end_dt = None
        
        # 1. Calculate Total Outward Supplies (Sales) from Checkouts using SQL aggregations
        # IMPORTANT: Filter by room_total > 0 to match Room Tariff Slab logic
        checkout_query = db.query(
            func.coalesce(func.sum(Checkout.grand_total), 0).label('total_outward_supplies'),
            func.coalesce(func.sum(
                case(
                    (Checkout.room_total <= 4999, Checkout.room_total / 1.05),
                    (Checkout.room_total < 7500, Checkout.room_total / 1.12),
                    else_=Checkout.room_total / 1.18
                )
            ), 0).label('room_taxable'),
            func.coalesce(func.sum(
                case(
                    (Checkout.room_total <= 4999, (Checkout.room_total - Checkout.room_total / 1.05) / 2),
                    (Checkout.room_total < 7500, (Checkout.room_total - Checkout.room_total / 1.12) / 2),
                    else_=(Checkout.room_total - Checkout.room_total / 1.18) / 2
                )
            ), 0).label('room_cgst_sgst'),
            func.coalesce(func.sum(Checkout.food_total / 1.05), 0).label('food_taxable'),
            func.coalesce(func.sum((Checkout.food_total - Checkout.food_total / 1.05) / 2), 0).label('food_cgst_sgst'),
            func.coalesce(func.sum(Checkout.service_total / 1.18), 0).label('service_taxable'),
            func.coalesce(func.sum((Checkout.service_total - Checkout.service_total / 1.18) / 2), 0).label('service_cgst_sgst'),
            func.coalesce(func.sum(
                case(
                    (Checkout.package_total < 7500, Checkout.package_total / 1.12),
                    else_=Checkout.package_total / 1.18
                )
            ), 0).label('package_taxable'),
            func.coalesce(func.sum(
                case(
                    (Checkout.package_total < 7500, (Checkout.package_total - Checkout.package_total / 1.12) / 2),
                    else_=(Checkout.package_total - Checkout.package_total / 1.18) / 2
                )
            ), 0).label('package_cgst_sgst')
        ).filter(Checkout.room_total > 0)  # Match Room Tariff Slab filter
        if start_dt:
            checkout_query = checkout_query.filter(Checkout.checkout_date >= start_dt)
        if end_dt:
            checkout_query = checkout_query.filter(Checkout.checkout_date <= end_dt)
        
        # Debug: Log query parameters and verify base data matches Room Tariff Slab
        # print(f"Master Summary: Date range - start_dt={start_dt}, end_dt={end_dt}")
        
        # Verify: Count checkouts that match Room Tariff Slab criteria
        verify_query = db.query(func.count(Checkout.id)).filter(Checkout.room_total > 0)
        if start_dt:
            verify_query = verify_query.filter(Checkout.checkout_date >= start_dt)
        if end_dt:
            verify_query = verify_query.filter(Checkout.checkout_date <= end_dt)
        checkout_count = verify_query.scalar() or 0
        # print(f"Master Summary: Found {checkout_count} checkouts with room_total > 0 (should match Room Tariff Slab)")
        
        result = checkout_query.first()
        
        # Debug: Log aggregation results
        # print(f"Master Summary: SQL Aggregation Result - outward_supplies={result.total_outward_supplies}, room_taxable={result.room_taxable}, room_cgst_sgst={result.room_cgst_sgst}")
        
        total_outward_supplies = float(result.total_outward_supplies or 0)
        total_taxable_value = float(result.room_taxable or 0) + float(result.food_taxable or 0) + float(result.service_taxable or 0) + float(result.package_taxable or 0)
        total_output_cgst = float(result.room_cgst_sgst or 0) + float(result.food_cgst_sgst or 0) + float(result.service_cgst_sgst or 0) + float(result.package_cgst_sgst or 0)
        total_output_sgst = total_output_cgst  # Same as CGST for intra-state
        total_output_igst = 0.0  # Assuming intra-state for now
        total_output_tax = total_output_igst + total_output_cgst + total_output_sgst
        
        # Debug: Log calculated totals
        # print(f"Master Summary: Calculated totals - outward_supplies={total_outward_supplies}, taxable_value={total_taxable_value}, output_tax={total_output_tax}")
        
        # 2. Calculate Total Input Tax Credit (ITC) from Purchases using SQL aggregations
        # Join with PurchaseDetail and InventoryItem/Category to filter eligible ITC
        purchase_query = db.query(
            func.coalesce(func.sum(
                case(
                    (
                        and_(
                            PurchaseDetail.item_id.isnot(None),
                            InventoryItem.category_id.isnot(None),
                            or_(
                                InventoryCategory.itc_eligibility.is_(None),
                                InventoryCategory.itc_eligibility == "Eligible",
                                ~InventoryCategory.itc_eligibility.contains("Ineligible"),
                                ~InventoryCategory.itc_eligibility.contains("Blocked")
                            )
                        ),
                        PurchaseDetail.igst_amount + PurchaseDetail.cgst_amount + PurchaseDetail.sgst_amount
                    ),
                    else_=0
                )
            ), 0).label('total_itc_eligible'),
            func.coalesce(func.sum(
                case(
                    (
                        and_(
                            PurchaseDetail.item_id.isnot(None),
                            InventoryItem.category_id.isnot(None),
                            or_(
                                InventoryCategory.itc_eligibility.is_(None),
                                InventoryCategory.itc_eligibility == "Eligible",
                                ~InventoryCategory.itc_eligibility.contains("Ineligible"),
                                ~InventoryCategory.itc_eligibility.contains("Blocked")
                            )
                        ),
                        PurchaseDetail.igst_amount
                    ),
                    else_=0
                )
            ), 0).label('total_itc_igst'),
            func.coalesce(func.sum(
                case(
                    (
                        and_(
                            PurchaseDetail.item_id.isnot(None),
                            InventoryItem.category_id.isnot(None),
                            or_(
                                InventoryCategory.itc_eligibility.is_(None),
                                InventoryCategory.itc_eligibility == "Eligible",
                                ~InventoryCategory.itc_eligibility.contains("Ineligible"),
                                ~InventoryCategory.itc_eligibility.contains("Blocked")
                            )
                        ),
                        PurchaseDetail.cgst_amount
                    ),
                    else_=0
                )
            ), 0).label('total_itc_cgst'),
            func.coalesce(func.sum(
                case(
                    (
                        and_(
                            PurchaseDetail.item_id.isnot(None),
                            InventoryItem.category_id.isnot(None),
                            or_(
                                InventoryCategory.itc_eligibility.is_(None),
                                InventoryCategory.itc_eligibility == "Eligible",
                                ~InventoryCategory.itc_eligibility.contains("Ineligible"),
                                ~InventoryCategory.itc_eligibility.contains("Blocked")
                            )
                        ),
                        PurchaseDetail.sgst_amount
                    ),
                    else_=0
                )
            ), 0).label('total_itc_sgst'),
            func.count(func.distinct(PurchaseMaster.id)).label('total_purchases')
        ).join(
            PurchaseDetail, PurchaseMaster.id == PurchaseDetail.purchase_master_id
        ).outerjoin(
            InventoryItem, PurchaseDetail.item_id == InventoryItem.id
        ).outerjoin(
            InventoryCategory, InventoryItem.category_id == InventoryCategory.id
        )
        
        if start_dt:
            purchase_date = start_dt.date() if isinstance(start_dt, datetime) else start_dt
            purchase_query = purchase_query.filter(PurchaseMaster.purchase_date >= purchase_date)
        if end_dt:
            purchase_date = end_dt.date() if isinstance(end_dt, datetime) else end_dt
            purchase_query = purchase_query.filter(PurchaseMaster.purchase_date <= purchase_date)
        
        itc_result = purchase_query.first()
        
        total_itc_eligible = float(itc_result.total_itc_eligible or 0)
        total_itc_igst = float(itc_result.total_itc_igst or 0)
        total_itc_cgst = float(itc_result.total_itc_cgst or 0)
        total_itc_sgst = float(itc_result.total_itc_sgst or 0)
        total_purchases_count = int(itc_result.total_purchases or 0)
        
        # 3. Calculate RCM Liability (from RCM Register)
        # For now, assume 0 - can be enhanced when RCM purchases are tracked
        total_rcm_liability = 0.0
        
        # 4. Calculate Net GST Payable
        net_gst_payable = total_output_tax - total_itc_eligible
        
        return {
            "period": {"start_date": start_date, "end_date": end_date},
            "total_outward_supplies": round(total_outward_supplies, 2),
            "total_taxable_value": round(total_taxable_value, 2),
            "total_output_tax": {
                "igst": round(total_output_igst, 2),
                "cgst": round(total_output_cgst, 2),
                "sgst": round(total_output_sgst, 2),
                "total": round(total_output_tax, 2)
            },
            "total_input_tax_credit": {
                "igst": round(total_itc_igst, 2),
                "cgst": round(total_itc_cgst, 2),
                "sgst": round(total_itc_sgst, 2),
                "total": round(total_itc_eligible, 2)
            },
            "net_gst_payable": round(net_gst_payable, 2),
            "total_rcm_liability": round(total_rcm_liability, 2),
            "summary": {
                "total_invoices": int(db.query(func.count(Checkout.id)).filter(
                    *([Checkout.checkout_date >= start_dt] if start_dt else []),
                    *([Checkout.checkout_date <= end_dt] if end_dt else [])
                ).scalar() or 0),
                "total_purchases": total_purchases_count,
                "output_tax_rate": round((total_output_tax / total_taxable_value * 100) if total_taxable_value > 0 else 0, 2),
                "itc_utilization_rate": round((total_itc_eligible / total_output_tax * 100) if total_output_tax > 0 else 0, 2)
            }
        }

    except Exception as e:
        import traceback
        print(f"Error in Master GST Summary: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error generating Master GST Summary: {str(e)}")

