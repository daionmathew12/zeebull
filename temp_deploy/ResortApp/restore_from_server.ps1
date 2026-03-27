$ErrorActionPreference = "Stop"

$RemoteHost = "34.30.59.169"
$RemoteUser = "basilabrahamaby"
$KeyPath = "$env:USERPROFILE\.ssh\gcp_key"
$RemoteDBUser = "orchid_user"
$RemoteDBPass = "admin123"
$RemoteDBName = "orchid_resort"

$LocalDBUser = "postgres"
$LocalDBPass = "qwerty123"
$LocalDBName = "orchiddb"
$LocalDumpFile = "server_dump.backup"

Write-Host "1. Dumping remote database..."
ssh -o StrictHostKeyChecking=no -i $KeyPath $RemoteUser@$RemoteHost "PGPASSWORD='$RemoteDBPass' pg_dump -U $RemoteDBUser -h localhost -F c -b -v -f /tmp/server_dump.backup $RemoteDBName"

Write-Host "2. Downloading dump file..."
# Removing local file if exists
if (Test-Path $LocalDumpFile) { Remove-Item $LocalDumpFile }
scp -o StrictHostKeyChecking=no -i $KeyPath "$RemoteUser@$RemoteHost`:/tmp/server_dump.backup" $LocalDumpFile

Write-Host "3. Terminating local connections..."
$env:PGPASSWORD = $LocalDBPass
# Terminate connections so we can modify the DB
try {
    psql -U $LocalDBUser -h localhost -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$LocalDBName' AND pid <> pg_backend_pid();"
} catch {
    Write-Host "Warning: Could not terminate connections or psql failed. Continuing..."
}

Write-Host "4. Restoring database..."
# Using --clean to drop existing objects
# Using --no-owner to prevent errors about missing 'orchid_user' role
# Using --no-acl to skip privilege restoration
pg_restore -U $LocalDBUser -h localhost -d $LocalDBName --clean --if-exists --no-owner --no-acl -v $LocalDumpFile

Write-Host "Done! Database synced from server."
