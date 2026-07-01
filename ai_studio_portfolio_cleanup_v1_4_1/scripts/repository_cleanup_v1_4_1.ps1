param(
    [string]$ProjectRoot = (Get-Location).Path
)

$ErrorActionPreference = "Stop"

$archiveDir = Join-Path $ProjectRoot "docs\archive\legacy-phase-files"
New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null

$keepRoot = @(
    "README.md",
    "CHANGELOG.md",
    "RELEASE_NOTES.md",
    "LICENSE",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "PORTFOLIO_SUMMARY.md",
    "INTERVIEW_GUIDE.md",
    "VALIDATION_GUIDE.md",
    "GITHUB_RELEASE_NOTES_V1_4.md",
    "DUAL_MODE_PORTFOLIO_V1_4_SETUP.md",
    "ROLLBACK_V1_4.md"
)

$patterns = @(
    "*_SETUP.md",
    "*_VALIDATION_REPORT.md",
    "CLOUD_EDITION_V*_SETUP.md",
    "CLOUD_EDITION_V*_VALIDATION_REPORT.md",
    "DUAL_MODE_V*_SETUP.md",
    "DUAL_MODE_V*_VALIDATION_REPORT.md"
)

$filesToMove = @()
foreach ($pattern in $patterns) {
    $filesToMove += Get-ChildItem -Path $ProjectRoot -Filter $pattern -File -ErrorAction SilentlyContinue
}

$filesToMove = $filesToMove | Sort-Object FullName -Unique | Where-Object {
    $keepRoot -notcontains $_.Name
}

foreach ($file in $filesToMove) {
    $destination = Join-Path $archiveDir $file.Name
    Move-Item -Path $file.FullName -Destination $destination -Force
    Write-Host "Archived $($file.Name)"
}

Write-Host "Cleanup complete. Archive folder: $archiveDir"
