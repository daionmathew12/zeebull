from fastapi import FastAPI
from app.database import Base, engine
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os


# API Routers
from app.api import (
    attendance,
    auth,
    booking,
    checkout,
    dashboard,
    employee,
    expenses,
    food_category,
    food_item,
    food_orders,
    frontend,
    packages,
    payment,
    report,
    role,
    room,
    reports,
    service,
    service_report,
    service_request,
    user,
    account,
    gst_reports,
    comprehensive_reports,
    notification
)

# Import recipe router separately to catch any import errors
recipe_module = None
try:
    from app.api import recipe as recipe_module
    print("[OK] Recipe router imported successfully in app.main")
    print(f"   Router prefix: {recipe_module.router.prefix}")
    print(f"   Number of routes: {len(recipe_module.router.routes)}")
except Exception as e:
    print(f"[ERROR] ERROR importing recipe router in app.main: {e}")
    import traceback
    traceback.print_exc()
    recipe_module = None

# Import inventory router separately to catch any import errors
try:
    from app.api import inventory
    print("[OK] Inventory router imported successfully in app.main")
except Exception as e:
    print(f"[ERROR] ERROR importing inventory router in app.main: {e}")
    import traceback
    traceback.print_exc()
    inventory = None

# Import public router separately to catch any import errors
# Force reload - public router should now work
public_module = None
try:
    from app.api import public as public_module
    print("[OK] Public router imported successfully in app.main")
    print(f"   Router prefix: {public_module.router.prefix}")
    print(f"   Number of routes: {len(public_module.router.routes)}")
except Exception as e:
    print(f"[ERROR] ERROR importing public router in app.main: {e}")
    import traceback
    traceback.print_exc()
    public_module = None

# Create DB tables
Base.metadata.create_all(bind=engine)

ROOT_PATH = os.getenv("ROOT_PATH", "")

app = FastAPI(root_path=ROOT_PATH, redirect_slashes=False)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file dirs
UPLOAD_DIR = "uploads/expenses"
os.makedirs("static/rooms", exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Register Public Router (no authentication required)
if public_module is not None:
    try:
        app.include_router(public_module.router, prefix="/api")
        print(f"[OK] Public router registered with {len(public_module.router.routes)} routes")
    except Exception as e:
        print(f"[ERROR] ERROR registering public router: {e}")
        import traceback
        traceback.print_exc()
else:
    print("[ERROR] Public router not imported, skipping registration")

# Register Routers with /api prefix to match nginx configuration
app.include_router(auth.router, prefix="/api")
app.include_router(user.router, prefix="/api")
app.include_router(role.router, prefix="/api")
app.include_router(employee.router, prefix="/api")
app.include_router(attendance.router, prefix="/api")
app.include_router(room.router, prefix="/api")
app.include_router(packages.router, prefix="/api")
app.include_router(booking.router, prefix="/api")
app.include_router(checkout.router, prefix="/api")
app.include_router(food_category.router, prefix="/api")
app.include_router(food_item.router, prefix="/api")
app.include_router(food_orders.router, prefix="/api")
# Include recipe router if it was imported successfully
if recipe_module is not None:
    try:
        app.include_router(recipe_module.router, prefix="/api")
        print(f"[OK] Recipe router registered in app.main with {len(recipe_module.router.routes)} routes")
        # Print all recipe routes for debugging
        for route in recipe_module.router.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = ', '.join(route.methods)
                print(f"   Registered: {methods} /api{route.path}")
    except Exception as e:
        print(f"[ERROR] ERROR registering recipe router in app.main: {e}")
        import traceback
        traceback.print_exc()
else:
    print("[ERROR] Recipe router not imported in app.main, skipping registration")
    print("   This means there was an import error. Check the error message above.")

# Add a simple test endpoint to verify server is running with latest code
@app.get("/api/test-server")
def test_server():
    """Test endpoint to verify server is running"""
    return {
        "message": "Server is running",
        "recipe_router_loaded": recipe_module is not None,
        "recipe_routes_count": len(recipe_module.router.routes) if recipe_module else 0
    }

app.include_router(service.router, prefix="/api")
app.include_router(service_report.router, prefix="/api")
app.include_router(service_request.router, prefix="/api")
app.include_router(expenses.router, prefix="/api")
app.include_router(payment.router, prefix="/api")
app.include_router(frontend.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(report.router, prefix="/api")

# Include the missing routers to fix 404 errors
app.include_router(account.router, prefix="/api")
app.include_router(gst_reports.router, prefix="/api")
app.include_router(comprehensive_reports.router, prefix="/api")
app.include_router(notification.router, prefix="/api")

# Include inventory router if it was imported successfully
if inventory is not None:
    try:
        app.include_router(inventory.router, prefix="/api")
        print(f"✅ Inventory router registered in app.main with {len(inventory.router.routes)} routes")
    except Exception as e:
        print(f"❌ ERROR registering inventory router in app.main: {e}")
        import traceback
        traceback.print_exc()
else:
    print("❌ Inventory router not imported in app.main, skipping registration")

# Include stock reconciliation router
print("DEBUG: About to import stock_reconciliation router...")
try:
    from app.api import stock_reconciliation
    print(f"DEBUG: Stock reconciliation module imported, has {len(stock_reconciliation.router.routes)} routes")
    app.include_router(stock_reconciliation.router, prefix="/api")
    print(f"✅ Stock reconciliation router registered with {len(stock_reconciliation.router.routes)} routes")
except Exception as e:
    print(f"❌ ERROR importing/registering stock reconciliation router: {e}")
    import traceback
    traceback.print_exc()

# app.include_router(guest_api.guest_router) # <--- And add this line
# app.include_router(billing_api.router) # <-- Now billing is active
