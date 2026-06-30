$ErrorActionPreference = "Stop"
python -m pip install -r requirements-e2e.txt
python -m playwright install chromium
$env:RUN_E2E = "1"
python -m pytest tests/e2e -q
