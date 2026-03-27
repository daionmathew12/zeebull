# Running Dashboard Locally with Server Data

This guide explains how to run the Orchid Resort Dashboard on your local machine with the same data from the production server.

## Prerequisites

Before you begin, ensure you have the following installed:

1. **PostgreSQL** (version 12 or higher)
   - Download from: https://www.postgresql.org/download/windows/
   - During installation, set the password for the `postgres` user to `qwerty123`
   - Make sure PostgreSQL is running on port `5432`

2. **Python** (version 3.8 or higher)
   - Download from: https://www.python.org/downloads/
   - Make sure to check "Add Python to PATH" during installation

3. **Node.js** (version 16 or higher)
   - Download from: https://nodejs.org/
   - This includes npm (Node Package Manager)

4. **SSH Access to Server**
   - Ensure you have the SSH key at: `%USERPROFILE%\.ssh\gcp_key`
   - Server IP: `34.134.50.147`
   - Username: `basilabrahamaby`

## Quick Start (Automated)

The easiest way to get started is to use the automated script:

```batch
run_dashboard_with_server_data.bat
```

This script will:
1. ✅ Backup the database from the server
2. ✅ Restore it to your local PostgreSQL
3. ✅ Start the backend API server
4. ✅ Start the dashboard frontend

## Manual Setup (Step-by-Step)

If you prefer to run each step manually or if the automated script fails:

### Step 1: Create Local Database

Open PowerShell and run:

```powershell
$env:PGPASSWORD = "qwerty123"
psql -U postgres -h localhost -c "CREATE DATABASE orchiddb;"
```

### Step 2: Backup and Restore Database from Server

Navigate to the ResortApp directory and run the restore script:

```powershell
cd "c:\releasing\New Orchid\ResortApp"
.\restore_from_server.ps1
```

This will:
- Connect to the production server
- Create a backup of the `orchid_resort` database
- Download it to your local machine
- Restore it to your local `orchiddb` database

**Note:** This process may take 2-5 minutes depending on the database size and network speed.

### Step 3: Install Backend Dependencies

If this is your first time running the backend, install dependencies:

```batch
cd "c:\releasing\New Orchid\ResortApp"
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
```

### Step 4: Start Backend Server

```batch
cd "c:\releasing\New Orchid\ResortApp"
call venv\Scripts\activate.bat
python main.py
```

The backend will start on: **http://localhost:8011**
API Documentation: **http://localhost:8011/docs**

### Step 5: Install Dashboard Dependencies

If this is your first time running the dashboard, install dependencies:

```batch
cd "c:\releasing\New Orchid\dasboard"
npm install
```

### Step 6: Start Dashboard Frontend

```batch
cd "c:\releasing\New Orchid\dasboard"
npm start
```

The dashboard will automatically open in your browser at: **http://localhost:3000**

## Configuration Files

### Backend Configuration (ResortApp/.env)

```env
DATABASE_URL=postgresql+psycopg2://postgres:qwerty123@localhost:5432/orchiddb
PORT=8011
ROOT_PATH=
SECRET_KEY=orchid-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
USE_LOCAL_POSTGRES_USER=false
```

### Server Connection Details (restore_from_server.ps1)

```powershell
$RemoteHost = "34.30.59.169"
$RemoteUser = "basilabrahamaby"
$RemoteDBUser = "orchid_user"
$RemoteDBPass = "admin123"
$RemoteDBName = "orchid_resort"
```

## Troubleshooting

### Issue: "psql: command not found"

**Solution:** Add PostgreSQL to your PATH:
1. Find your PostgreSQL installation (usually `C:\Program Files\PostgreSQL\15\bin`)
2. Add it to your system PATH environment variable
3. Restart your terminal

### Issue: "Connection refused" when connecting to PostgreSQL

**Solution:** 
1. Check if PostgreSQL service is running:
   - Open Services (Win + R, type `services.msc`)
   - Look for "postgresql-x64-15" (or your version)
   - Make sure it's running
2. Verify the password is correct (`qwerty123`)

### Issue: "SSH connection failed"

**Solution:**
1. Verify the SSH key exists at `%USERPROFILE%\.ssh\gcp_key`
2. Check the key permissions
3. Test SSH connection manually:
   ```powershell
   ssh -i %USERPROFILE%\.ssh\gcp_key basilabrahamaby@34.30.59.169
   ```

### Issue: Backend fails to start with "ModuleNotFoundError"

**Solution:**
1. Make sure you activated the virtual environment
2. Reinstall dependencies:
   ```batch
   cd ResortApp
   call venv\Scripts\activate.bat
   pip install -r requirements.txt
   ```

### Issue: Dashboard shows "Network Error" or can't connect to API

**Solution:**
1. Verify the backend is running on http://localhost:8011
2. Check the backend logs for errors
3. Ensure no firewall is blocking port 8011

### Issue: Dashboard npm install fails

**Solution:**
1. Clear npm cache:
   ```batch
   npm cache clean --force
   ```
2. Delete node_modules and package-lock.json:
   ```batch
   cd dasboard
   rmdir /s /q node_modules
   del package-lock.json
   npm install
   ```

## Updating Data from Server

To refresh your local database with the latest server data, simply run:

```powershell
cd "c:\releasing\New Orchid\ResortApp"
.\restore_from_server.ps1
```

**Note:** This will overwrite your local database with the server data. Any local changes will be lost.

## Default Login Credentials

After restoring the database, you can log in with the admin credentials from the server. If you don't know them, you can create a new admin user:

```batch
cd "c:\releasing\New Orchid\ResortApp"
call venv\Scripts\activate.bat
python create_admin.py
```

## Stopping the Servers

To stop the servers:
1. Press `Ctrl+C` in the backend terminal window
2. Press `Ctrl+C` in the dashboard terminal window

## Additional Resources

- **Backend API Documentation:** http://localhost:8011/docs (when running)
- **ResortApp Directory:** `c:\releasing\New Orchid\ResortApp`
- **Dashboard Directory:** `c:\releasing\New Orchid\dasboard`
- **Database Backups:** Stored as `server_dump.backup` in ResortApp directory

## Next Steps

Once everything is running:
1. Open http://localhost:3000 in your browser
2. Log in with your credentials
3. You should see all the data from the production server
4. Any changes you make will only affect your local database

---

**Last Updated:** 2026-02-14
