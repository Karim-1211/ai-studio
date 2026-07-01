# AI Studio Portfolio Cleanup v1.4.1 Validation Guide

## Validation checklist

Run after copying the package into the project:

```powershell
python -m compileall -q .
Test-Path "docs/archive/legacy-phase-files"
git status
```

Expected:

- `python -m compileall -q .` prints no output
- archive folder exists
- old setup/validation files show as moved or renamed in Git
- application source files remain unchanged unless already modified before cleanup

## Functional validation

Because this release only reorganizes documentation files, no database migration or app redeploy behavior change is expected.

Still verify after push:

- GitHub README loads correctly
- `docs/` folder is visible
- archived files are inside `docs/archive/legacy-phase-files/`
- Render remains live
