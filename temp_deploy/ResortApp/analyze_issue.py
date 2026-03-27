
import sys
import os
from sqlalchemy import func

# Add root directory to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.inventory import StockIssue, StockIssueDetail, Location

def analyze_issue_12():
    db = SessionLocal()
    try:
        print("--- Analyzing Stock Issue #12 ---")
        issue = db.query(StockIssue).filter(StockIssue.id == 12).first()
        if not issue:
            print("Issue #12 not found")
            return

        print(f"Issue ID: {issue.id} | Number: {issue.issue_number}")
        print(f"Source Loc ID: {issue.source_location_id}")
        print(f"Dest Loc ID: {issue.destination_location_id}")
        
        if issue.destination_location_id:
            dest = db.query(Location).filter(Location.id == issue.destination_location_id).first()
            print(f"Dest Name: {dest.name}")
        else:
            print("Dest Loc is NONE")

        print("Details:")
        for d in issue.details:
             print(f"- Item: {d.item_id} | Qty: {d.issued_quantity} | Cost: {d.cost}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    analyze_issue_12()
