# Final Workspace, Docker, and GitHub Setup

This package combines the compact workspace redesign with Docker and GitHub portfolio packaging.

## What changes in the interface

- The AI Assistant header is reduced to a slim toolbar.
- Knowledge Sources becomes a narrow summary bar.
- Chat and global documents move into a right-side drawer.
- The drawer is closed on first use and remembers its most recent state.
- The drawer includes separate Chat Documents and Global Library tabs.
- The System Status panel floats over the workspace instead of pushing the chat down.
- Existing selections, uploads, OCR, RAG, citations, settings, and chat history remain unchanged.

## Files added

- `README.md`
- `Dockerfile`
- `docker-entrypoint.sh`
- `compose.yaml`
- `compose.ollama.yaml`
- `.dockerignore`
- `.env.docker.example`
- `requirements-dev.txt`
- `.github/workflows/ci.yml`
- `docs/ARCHITECTURE.md`
- `docs/DOCKER.md`
- `docs/GITHUB.md`
- `RELEASE_CHECKLIST.md`

## Main files changed

- `templates/index.html`
- `static/style.css`
- `static/js/ui.js`
- `static/js/documents.js`
- `static/js/system_status.js`
- `requirements.txt`
- `.gitignore`
- `PROJECT_ROADMAP.md`

## Replace your project

Stop AI Studio:

```powershell
Ctrl + C
```

Assuming the extracted update folder is in Downloads:

```powershell
$source = "$env:USERPROFILE\Downloads\ai_studio_final_workspace"
$project = "C:\Path\To\AI-Chat-App"

Test-Path $source
```

After it returns `True`, copy the package:

```powershell
robocopy $source $project /E `
  /XD .venv venv uploads logs .git .idea __pycache__ .pytest_cache `
  /XF .env .env.docker *.pyc
```

Confirm `FAILED` is `0` in the Robocopy summary.

## Install development dependencies

```powershell
cd "C:\Path\To\AI-Chat-App"
python -m pip install -r requirements-dev.txt
```

## Validate before starting

```powershell
python -m compileall -q .
python -m pytest
```

When Node.js is installed, validate browser JavaScript:

```powershell
Get-ChildItem static\js\*.js | ForEach-Object {
  node --check $_.FullName
}
```

## Start locally

```powershell
python app.py
```

Open `http://127.0.0.1:5000` and press `Ctrl + F5`.

### Interface test

1. Confirm the header is compact.
2. Confirm Knowledge Sources is a single narrow row.
3. Click `Manage`.
4. Switch between Chat Documents and Global Library.
5. Close the drawer with `×`, the backdrop, or Escape.
6. Refresh the page and confirm the last drawer state is remembered.
7. Ask a RAG question while the drawer is closed.
8. Confirm selected documents still provide citations.
9. Open System Status and confirm it floats over the workspace.

## Docker setup

Copy the example:

```powershell
Copy-Item .env.docker.example .env.docker
```

Generate two URL-safe values:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Put the first in `POSTGRES_PASSWORD` and the second in `SECRET_KEY`.

With Ollama running on Windows:

```powershell
docker compose --env-file .env.docker up --build -d
```

Open `http://127.0.0.1:5000`.

Detailed Docker instructions are in `docs/DOCKER.md`.

## GitHub setup

Before committing:

```powershell
git status
```

Confirm `.env`, `.env.docker`, uploaded files, logs, and the virtual environment are absent.

Initialize and commit:

```powershell
git init
git add .
git commit -m "Build AI Studio local RAG workspace"
git branch -M main
```

Follow `docs/GITHUB.md` for remote setup, CI, screenshots, and release preparation.
