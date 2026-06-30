param(
    [Parameter(Mandatory=$true)]
    [string]$BackupFile,

    [Parameter(Mandatory=$true)]
    [string]$TargetDatabaseUrl
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $BackupFile)) {
    throw "Backup file not found: $BackupFile"
}

if ($env:DATABASE_URL -and $TargetDatabaseUrl -eq $env:DATABASE_URL) {
    throw "The rehearsal target must not be the live AI Studio database."
}

pg_restore `
  --clean `
  --if-exists `
  --no-owner `
  --no-privileges `
  --dbname=$TargetDatabaseUrl `
  $BackupFile

Write-Host "Restore rehearsal completed against the separate target database."
