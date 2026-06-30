param(
    [string]$OutputDirectory = "$env:USERPROFILE\Documents\AI-Studio-Backups"
)

$ErrorActionPreference = "Stop"

if (-not $env:DATABASE_URL) {
    throw "DATABASE_URL is not set in this PowerShell session. Load it safely before running this script."
}

New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupFile = Join-Path $OutputDirectory "ai-studio-$timestamp.dump"

pg_dump `
  --format=custom `
  --no-owner `
  --no-privileges `
  --file=$backupFile `
  $env:DATABASE_URL

Write-Host "Backup created: $backupFile"
