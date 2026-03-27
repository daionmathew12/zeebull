# API Endpoints Summary

## Dashboard Endpoints (`/api/dashboard`)
- `GET /api/dashboard/kpis` - Basic KPIs
- `GET /api/dashboard/summary?period={all|day|week|month}` - Comprehensive KPIs with department-wise breakdown
- `GET /api/dashboard/charts` - Chart data
- `GET /api/dashboard/reports` - Reports data

## Account Endpoints (`/api/accounts`)
- `GET /api/accounts/groups` - Account groups
- `GET /api/accounts/ledgers` - Account ledgers
- `GET /api/accounts/trial-balance?automatic=true` - Trial balance
- `GET /api/accounts/comprehensive-report` - Comprehensive report
- `POST /api/accounts/journal-entries` - Create journal entry
- `GET /api/accounts/journal-entries` - Get journal entries
- `POST /api/accounts/fix-missing-journal-entries` - Fix missing entries

## GST Reports (`/api/gst-reports`)
- `GET /api/gst-reports/master-summary` - Master GST summary
- `GET /api/gst-reports/b2b-sales` - B2B sales register
- `GET /api/gst-reports/b2c-sales` - B2C sales register
- `GET /api/gst-reports/hsn-sac-summary` - HSN/SAC summary
- `GET /api/gst-reports/itc-register` - ITC register
- `GET /api/gst-reports/rcm-register` - RCM register
- `GET /api/gst-reports/advance-receipt` - Advance receipt report
- `GET /api/gst-reports/room-tariff-slab` - Room tariff slab report

## Comprehensive Reports (`/api/reports/comprehensive`)
- `GET /api/reports/comprehensive/summary` - Summary
- `GET /api/reports/comprehensive/inventory/category-wise` - Category-wise inventory
- `GET /api/reports/comprehensive/inventory/department-wise` - Department-wise inventory
- `GET /api/reports/comprehensive/bookings` - Bookings
- `GET /api/reports/comprehensive/package-bookings` - Package bookings
- `GET /api/reports/comprehensive/expenses` - Expenses
- `GET /api/reports/comprehensive/food-orders` - Food orders
- `GET /api/reports/comprehensive/purchases` - Purchases
- `GET /api/reports/comprehensive/vendors` - Vendors
- `GET /api/reports/comprehensive/services` - Services

## Department Reports (`/api/reports/department`)
- Multiple endpoints for Front Office, Restaurant, Inventory, Housekeeping, Security & HR, Management reports

## Other Key Endpoints
- `/api/rooms` - Room management
- `/api/bookings` - Booking management
- `/api/employees` - Employee management
- `/api/expenses` - Expense management
- `/api/food-orders` - Food order management
- `/api/services` - Service management
- `/api/inventory` - Inventory management

## Fixed Issues
1. ✅ Fixed `FoodOrder.total_amount` → `FoodOrder.amount` in department KPIs
2. ✅ Added comprehensive error handling for department KPIs
3. ✅ Added error logging for debugging
4. ✅ Verified all model fields exist

