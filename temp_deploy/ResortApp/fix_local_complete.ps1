
$ErrorActionPreference = "Stop"

Write-Host "--- 1. Restoring Database from Server ---"
try {
    .\restore_from_server.ps1
} catch {
    Write-Host "Error during restore: $_"
    exit 1
}

Write-Host "`n--- 2. Fixing Room 103 Counts ---"
try {
    python fix_103_counts.py
} catch {
    Write-Host "Error fixing counts: $_"
    # Don't exit, try next fix
}

Write-Host "`n--- 3. Fixing Room 103 Data/Status ---"
try {
    python fix_room_103.py
} catch {
    Write-Host "Error fixing data: $_"
}

Write-Host "`n--- 4. Checking DB Inventory State ---"
try {
    python check_db_inventory.py
} catch {
    Write-Host "Error checking inventory: $_"
}

Write-Host "`n--- Local Environment Fix Completed ---"
