# AI Studio Portfolio Cleanup v1.4.1 Setup Guide

This release cleans the GitHub repository root without changing application logic.

## What it does

- Moves old setup and validation reports into `docs/archive/legacy-phase-files/`
- Keeps the repository root focused on product files and source code
- Preserves all old documentation instead of deleting it
- Does not change database migrations
- Does not change Render configuration
- Does not change AI, RAG, OCR, upload, or authentication code

## Files intentionally kept in root

- README.md
- CHANGELOG.md
- RELEASE_NOTES.md
- LICENSE
- CONTRIBUTING.md
- SECURITY.md
- PORTFOLIO_SUMMARY.md
- INTERVIEW_GUIDE.md
- VALIDATION_GUIDE.md
- GITHUB_RELEASE_NOTES_V1_4.md
- DUAL_MODE_PORTFOLIO_V1_4_SETUP.md
- ROLLBACK_V1_4.md
- app.py
- config.py
- render.yaml
- Dockerfile
- compose.yaml
- compose.ollama.yaml
- requirements files
- main application folders

## Files archived

The cleanup script archives legacy files matching these patterns:

- `*_SETUP.md`
- `*_VALIDATION_REPORT.md`
- `CLOUD_EDITION_V*_SETUP.md`
- `CLOUD_EDITION_V*_VALIDATION_REPORT.md`
- `DUAL_MODE_V*_SETUP.md`
- `DUAL_MODE_V*_VALIDATION_REPORT.md`

except for the current v1.4 portfolio files listed above.

## Install steps

Run the commands from the assistant message exactly.

## Rollback

If you want to undo the cleanup before committing, run:

```powershell
git restore .
git clean -fd
```

If already committed but not pushed:

```powershell
git reset --hard HEAD~1
```

If already pushed, ask ChatGPT for a safe revert command.
