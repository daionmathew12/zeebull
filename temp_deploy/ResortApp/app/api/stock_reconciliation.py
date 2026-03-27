"""
Stock Reconciliation Endpoint
Fixes discrepancies between global stock and location stocks
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.utils.auth import get_current_user
from typing import List, Dict, Any
from datetime import datetime
from app.utils.branch_scope import get_branch_id

router = APIRouter()


@router.post("/inventory/reconcile-stock")
def reconcile_stock(
    fix_discrepancies: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):
    """
    Reconcile stock discrepancies between global and location stocks.
    
    Args:
        fix_discrepancies: If True, automatically fix discrepancies. If False, only report them.
    
    Returns:
        Report of discrepancies found and actions taken
    """
    from app.models.inventory import InventoryItem, LocationStock, InventoryTransaction
    from sqlalchemy import func
    
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "total_items_checked": 0,
        "discrepancies_found": 0,
        "discrepancies_fixed": 0,
        "items_with_issues": [],
        "summary": {}
    }
    
    try:
        # Get all inventory items
        items = db.query(InventoryItem).filter(InventoryItem.branch_id == branch_id).all()
        report["total_items_checked"] = len(items)
        
        for item in items:
            # Calculate total stock across all locations
            location_stocks = db.query(LocationStock).filter(
                LocationStock.item_id == item.id,
                LocationStock.branch_id == branch_id
            ).all()
            
            total_location_stock = sum(ls.quantity for ls in location_stocks)
            global_stock = item.current_stock or 0
            
            # Check for discrepancy
            discrepancy = global_stock - total_location_stock
            
            if abs(discrepancy) > 0.01:  # Allow for small floating point errors
                report["discrepancies_found"] += 1
                
                issue_detail = {
                    "item_id": item.id,
                    "item_name": item.name,
                    "item_code": item.item_code,
                    "global_stock": float(global_stock),
                    "total_location_stock": float(total_location_stock),
                    "discrepancy": float(discrepancy),
                    "locations": [
                        {
                            "location_id": ls.location_id,
                            "location_name": ls.location.name if ls.location else f"Location {ls.location_id}",
                            "quantity": float(ls.quantity)
                        }
                        for ls in location_stocks
                    ],
                    "action_taken": None
                }
                
                # Fix if requested
                if fix_discrepancies:
                    # Strategy: Trust location stocks as source of truth
                    # Update global stock to match sum of location stocks
                    old_global = item.current_stock
                    item.current_stock = total_location_stock
                    
                    # Create adjustment transaction
                    adjustment_txn = InventoryTransaction(
                        item_id=item.id,
                        transaction_type="adjustment",
                        quantity=abs(discrepancy),
                        unit_price=item.unit_price,
                        total_amount=abs(discrepancy) * (item.unit_price or 0),
                        reference_number=f"RECONCILE-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                        notes=f"Stock reconciliation: Global {old_global} → {total_location_stock} (Discrepancy: {discrepancy})",
                        created_by=current_user.id,
                        branch_id=branch_id
                    )
                    db.add(adjustment_txn)
                    
                    issue_detail["action_taken"] = f"Adjusted global stock from {old_global} to {total_location_stock}"
                    report["discrepancies_fixed"] += 1
                else:
                    issue_detail["action_taken"] = "No action (fix_discrepancies=False)"
                
                report["items_with_issues"].append(issue_detail)
        
        # Commit changes if fixing
        if fix_discrepancies:
            db.commit()
            report["summary"]["status"] = "Fixed"
            report["summary"]["message"] = f"Fixed {report['discrepancies_fixed']} discrepancies"
        else:
            report["summary"]["status"] = "Report Only"
            report["summary"]["message"] = f"Found {report['discrepancies_found']} discrepancies (not fixed)"
        
        return report
        
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error during stock reconciliation: {str(e)}"
        )


@router.get("/inventory/stock-audit")
def stock_audit(
    item_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):
    """
    Detailed stock audit for an item or all items.
    Shows transaction history and current state.
    """
    from app.models.inventory import InventoryItem, LocationStock, InventoryTransaction
    from sqlalchemy import func
    
    if item_id:
        items = [db.query(InventoryItem).filter(InventoryItem.id == item_id, InventoryItem.branch_id == branch_id).first()]
        if not items[0]:
            raise HTTPException(status_code=404, detail="Item not found")
    else:
        items = db.query(InventoryItem).filter(InventoryItem.branch_id == branch_id).limit(100).all()  # Limit for performance
    
    audit_results = []
    
    for item in items:
        # Get all transactions for this item
        transactions = db.query(InventoryTransaction).filter(
            InventoryTransaction.item_id == item.id,
            InventoryTransaction.branch_id == branch_id
        ).order_by(InventoryTransaction.created_at.desc()).all()
        
        # Calculate expected stock from transactions
        calculated_stock = 0.0
        for txn in reversed(transactions):  # Process in chronological order
            if txn.transaction_type in ["in", "adjustment", "transfer_in", "return"]:
                calculated_stock += txn.quantity
            elif txn.transaction_type in ["out", "transfer_out"]:
                calculated_stock -= txn.quantity
        
        # Get location stocks
        location_stocks = db.query(LocationStock).filter(
            LocationStock.item_id == item.id,
            LocationStock.branch_id == branch_id
        ).all()
        
        total_location_stock = sum(ls.quantity for ls in location_stocks)
        
        audit_results.append({
            "item_id": item.id,
            "item_name": item.name,
            "item_code": item.item_code,
            "global_stock": float(item.current_stock or 0),
            "calculated_from_transactions": float(calculated_stock),
            "total_location_stock": float(total_location_stock),
            "discrepancies": {
                "global_vs_calculated": float((item.current_stock or 0) - calculated_stock),
                "global_vs_locations": float((item.current_stock or 0) - total_location_stock),
                "calculated_vs_locations": float(calculated_stock - total_location_stock)
            },
            "transaction_count": len(transactions),
            "location_count": len(location_stocks),
            "locations": [
                {
                    "location_id": ls.location_id,
                    "location_name": ls.location.name if ls.location else f"Location {ls.location_id}",
                    "quantity": float(ls.quantity),
                    "last_updated": ls.last_updated.isoformat() if ls.last_updated else None
                }
                for ls in location_stocks
            ],
            "recent_transactions": [
                {
                    "id": txn.id,
                    "type": txn.transaction_type,
                    "quantity": float(txn.quantity),
                    "reference": txn.reference_number,
                    "notes": txn.notes,
                    "created_at": txn.created_at.isoformat() if txn.created_at else None
                }
                for txn in transactions[:10]  # Last 10 transactions
            ]
        })
    
    return {
        "audit_date": datetime.utcnow().isoformat(),
        "items_audited": len(audit_results),
        "results": audit_results
    }


@router.post("/inventory/validate-checkout-stock")
def validate_checkout_stock(
    room_number: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    branch_id: int = Depends(get_branch_id)
):
    """
    Validate stock for a room before checkout.
    Ensures stock quantities are consistent and no negative stock exists.
    """
    from app.models.room import Room
    from app.models.inventory import LocationStock, StockIssue, StockIssueDetail
    
    room = db.query(Room).filter(Room.number == room_number, Room.branch_id == branch_id).first()
    if not room:
        raise HTTPException(status_code=404, detail=f"Room {room_number} not found")
    
    if not room.inventory_location_id:
        return {
            "room_number": room_number,
            "status": "no_inventory_location",
            "message": "Room has no inventory location assigned"
        }
    
    # Get all stock in room
    room_stocks = db.query(LocationStock).filter(
        LocationStock.location_id == room.inventory_location_id,
        LocationStock.branch_id == branch_id
    ).all()
    
    validation_results = {
        "room_number": room_number,
        "location_id": room.inventory_location_id,
        "total_items": len(room_stocks),
        "issues": [],
        "warnings": [],
        "stock_summary": []
    }
    
    for stock in room_stocks:
        item = stock.item
        if not item:
            continue
        
        # Check for negative stock
        if stock.quantity < 0:
            validation_results["issues"].append({
                "item_id": item.id,
                "item_name": item.name,
                "issue": "negative_stock",
                "quantity": float(stock.quantity),
                "message": f"Negative stock detected: {stock.quantity}"
            })
        
        # Get original issue quantity
        issues = db.query(StockIssueDetail).join(StockIssue).filter(
            StockIssue.destination_location_id == room.inventory_location_id,
            StockIssueDetail.item_id == item.id,
            StockIssue.branch_id == branch_id
        ).all()
        
        total_issued = sum(detail.issued_quantity for detail in issues)
        
        # Warn if current stock exceeds issued (shouldn't happen)
        if stock.quantity > total_issued:
            validation_results["warnings"].append({
                "item_id": item.id,
                "item_name": item.name,
                "warning": "stock_exceeds_issued",
                "current_stock": float(stock.quantity),
                "total_issued": float(total_issued),
                "message": f"Current stock ({stock.quantity}) exceeds total issued ({total_issued})"
            })
        
        validation_results["stock_summary"].append({
            "item_id": item.id,
            "item_name": item.name,
            "current_stock": float(stock.quantity),
            "total_issued": float(total_issued),
            "status": "ok" if stock.quantity >= 0 and stock.quantity <= total_issued else "issue"
        })
    
    validation_results["status"] = "ok" if not validation_results["issues"] else "has_issues"
    
    return validation_results
