# Booking Amount Fix - Deployment Guide

## Problem
Booking amounts were showing as ₹0 in the Flutter employee app due to:
1. Missing `total_amount` column in `package_bookings` table
2. Missing leave balance columns in `employees` table  
3. Missing `/auth/me` endpoint causing 404 errors
4. No self-healing logic to recalculate amounts for legacy bookings

## Solution Applied

### 1. Database Schema Changes

**File: `add_total_amount_column.py`** (Run on server)
- Adds `total_amount FLOAT DEFAULT 0.0` column to `package_bookings` table

**File: `add_employee_leave_columns.py`** (Run on server)
- Adds `paid_leave_balance INTEGER DEFAULT 12` to `employees` table
- Adds `sick_leave_balance INTEGER DEFAULT 12` to `employees` table
- Adds `long_leave_balance INTEGER DEFAULT 5` to `employees` table
- Adds `wellness_leave_balance INTEGER DEFAULT 5` to `employees` table

### 2. Backend Code Changes

**File: `ResortApp/app/models/Package.py`** (Lines 57-60)
- Added `total_amount = Column(Float, default=0.0)` to `PackageBooking` model

**File: `ResortApp/app/schemas/packages.py`** (Lines 83-85)
- Added `total_amount: Optional[float] = 0.0` to `PackageBookingOut` schema

**File: `ResortApp/app/curd/packages.py`** (Lines 262-280)
- Calculate `total_amount = package_price * stay_nights * num_rooms`
- Store calculated amount when creating package bookings

**File: `ResortApp/app/api/booking.py`** (Lines 146-188, 372-400)
- Added self-healing logic in `get_bookings` endpoint
- Recalculates and persists `total_amount` if it's 0 or None for regular bookings
- Includes robust date parsing

**File: `ResortApp/app/api/packages.py`** (Lines 468-488)
- Added self-healing logic in `get_bookings` endpoint for package bookings
- Recalculates and persists `total_amount` if it's 0 or None

**File: `ResortApp/app/api/auth.py`** (Lines 88-122)
- Added new `GET /auth/me` endpoint
- Returns authenticated user's profile with employee details
- Includes leave balance information

### 3. Frontend Code Changes

**File: `Mobile/employee/lib/presentation/screens/manager/manager_bookings_screen.dart`**
- Fixed field access for email/phone (`guest_email`, `guest_mobile`)
- Applied safe parsing for `total_amount`: `double.tryParse((value ?? 0).toString()) ?? 0`
- Prevents type mismatch errors from JSON response

**File: `Mobile/employee/lib/core/constants/api_constants.dart`**
- Switched `baseUrl` back to production: `https://teqmates.com/orchidapi/api`

## Deployment Instructions

### On Production Server (via SSH):

```bash
# 1. Navigate to project
cd /var/www/resort/orchid_production/ResortApp

# 2. Activate virtual environment
source venv/bin/activate

# 3. Pull latest code
git stash  # Save any local changes
git pull origin main  # or your branch name

# 4. Run database migration scripts
python3 add_total_amount_column.py
python3 add_employee_leave_columns.py

# 5. Restart the service
sudo systemctl restart orchid

# 6. Verify service is running
sudo systemctl status orchid
```

### Alternative: Use the deployment script

```bash
# Upload deploy_booking_fix.sh to server
# Then run:
chmod +x deploy_booking_fix.sh
./deploy_booking_fix.sh
```

## Testing

After deployment:
1. Open Flutter employee app
2. Login with manager credentials
3. Navigate to Manager Bookings screen
4. Verify booking amounts display correctly (not ₹0)
5. Check booking details modal shows correct total amount
6. Verify no 404 errors for `/auth/me` endpoint

## Files Modified

### Backend (ResortApp/)
- `app/models/Package.py`
- `app/schemas/packages.py`
- `app/curd/packages.py`
- `app/api/booking.py`
- `app/api/packages.py`
- `app/api/auth.py`

### Frontend (Mobile/employee/)
- `lib/presentation/screens/manager/manager_bookings_screen.dart`
- `lib/core/constants/api_constants.dart`

### Database Scripts (ResortApp/)
- `add_total_amount_column.py` (new)
- `add_employee_leave_columns.py` (new)

## Rollback Plan

If issues occur:
```bash
# Revert code
cd /var/www/resort/orchid_production/ResortApp
git reset --hard HEAD~1

# Remove columns (if needed)
psql -U orchiduser -d orchiddb
ALTER TABLE package_bookings DROP COLUMN IF EXISTS total_amount;
ALTER TABLE employees DROP COLUMN IF EXISTS paid_leave_balance;
ALTER TABLE employees DROP COLUMN IF EXISTS sick_leave_balance;
ALTER TABLE employees DROP COLUMN IF EXISTS long_leave_balance;
ALTER TABLE employees DROP COLUMN IF EXISTS wellness_leave_balance;

# Restart service
sudo systemctl restart orchid
```
