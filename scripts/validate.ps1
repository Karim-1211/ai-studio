$ErrorActionPreference = "Stop"

Write-Host "Checking Python syntax..."
python -m compileall -q .

if (Get-Command node -ErrorAction SilentlyContinue) {
    Write-Host "Checking JavaScript syntax..."
    Get-ChildItem static\js\*.js | ForEach-Object {
        node --check $_.FullName
    }
} else {
    Write-Warning "Node.js was not found; JavaScript syntax checks were skipped."
}

Write-Host "Running tests..."
python -m pytest

Write-Host "Validation completed successfully."
