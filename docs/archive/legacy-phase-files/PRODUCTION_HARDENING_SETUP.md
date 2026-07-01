# AI Studio — Production Hardening and Automated Testing

This update keeps the existing chats, messages, documents, global library, OCR, settings, and RAG features.

## Added

- Flask application factory
- Development, testing, and production configurations
- Flask-Migrate and Alembic baseline migration
- Detailed health checks
- System-status panel in the interface
- Structured rotating JSON logs
- Request IDs and request timing
- Security headers
- Safer API validation
- Transaction-aware uploaded-file deletion
- Orphan-upload cleanup command
- Automated pytest coverage for core routes
- Waitress production server for Windows
- `.env.example`

## Files and folders added

- `.env.example`
- `wsgi.py`
- `serve.py`
- `pytest.ini`
- `migrations/`
- `tests/`
- `routes/health_routes.py`
- `services/api_utils.py`
- `services/deletion_service.py`
- `services/health_service.py`
- `services/logging_service.py`
- `static/js/system_status.js`

The ZIP also contains complete replacement copies of the existing project files.

---

## 1. Stop Flask

Press:

```powershell
Ctrl + C
```

## 2. Extract this ZIP

The extracted folder should be:

```text
ai_studio_production_hardening
```

## 3. Copy the update into the project

Run in the PyCharm terminal:

```powershell
$source = "$env:USERPROFILE\Downloads\ai_studio_production_hardening"
$project = "C:\Path\To\AI-Chat-App"

Test-Path $source
```

It must return:

```text
True
```

Copy the update:

```powershell
robocopy $source $project /E `
  /XD .venv venv uploads .git .idea __pycache__ .pytest_cache logs `
  /XF .env *.pyc
```

Robocopy may return exit codes from 0 through 7 even when the copy succeeded. Review the summary and confirm `FAILED` is `0`.

The command does not replace:

- `.env`
- uploaded knowledge files
- the virtual environment
- Git data
- PyCharm settings
- logs

## 4. Install the new packages

```powershell
cd "C:\Path\To\AI-Chat-App"
python -m pip install -r requirements.txt
```

New packages include:

- Flask-Migrate
- Waitress
- pytest
- pytest-cov

## 5. Add production settings to `.env`

Generate a strong secret:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy the generated value into the existing `.env`:

```env
APP_ENV=development
SECRET_KEY=PASTE_THE_GENERATED_VALUE_HERE
AUTO_CREATE_DATABASE=true
LOG_LEVEL=INFO
SECURITY_HEADERS_ENABLED=true
ENABLE_HSTS=false
TRUST_PROXY_HEADERS=false
```

Keep the existing database, Ollama, embedding, and OCR settings.

Do not use `ENABLE_HSTS=true` until the application is served through HTTPS.

## 6. Register the existing database with Alembic

Your PostgreSQL tables already exist. Do not run `db upgrade` before stamping this existing database.

Check the migration state:

```powershell
python -m flask --app app:create_app db current
```

For the current existing database, run once:

```powershell
python -m flask --app app:create_app db stamp head
```

Confirm:

```powershell
python -m flask --app app:create_app db current
```

Expected revision:

```text
20260628_0001 (head)
```

For a completely empty future database, use this instead:

```powershell
python -m flask --app app:create_app db upgrade
```

## 7. Run the automated tests

```powershell
python -m pytest
```

Expected:

```text
11 passed
```

The tests use a temporary SQLite database and do not modify the PostgreSQL database.

## 8. Start development mode

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

Refresh with:

```text
Ctrl + F5
```

## 9. Test the system-status panel

The header now contains a status button.

Open it and verify:

- Database
- Ollama
- Embeddings
- OCR
- Upload storage

Direct health endpoints:

```text
http://127.0.0.1:5000/api/health/live
http://127.0.0.1:5000/api/health
http://127.0.0.1:5000/api/health/ready
```

`/api/health/ready` returns HTTP 503 when an essential dependency is unavailable.

## 10. Check logs

Application logs are written to:

```text
logs/ai_studio.log
```

The logs use JSON lines and include:

- UTC timestamp
- severity
- request ID
- method
- path
- status code
- response time

## 11. Check orphan uploads

List files that exist in `uploads` but are not referenced by PostgreSQL:

```powershell
python -m flask --app app:create_app cleanup-uploads
```

Delete confirmed orphan files:

```powershell
python -m flask --app app:create_app cleanup-uploads --delete
```

Run the listing command first.

## 12. Run with Waitress on Windows

After development testing passes, change `.env`:

```env
APP_ENV=production
AUTO_CREATE_DATABASE=false
```

Start the production WSGI server:

```powershell
python serve.py
```

Default address:

```text
http://127.0.0.1:5000
```

Optional server settings:

```env
HOST=127.0.0.1
PORT=5000
WAITRESS_THREADS=8
```

Stop Waitress with:

```text
Ctrl + C
```

To return to Flask development mode:

```env
APP_ENV=development
AUTO_CREATE_DATABASE=true
```

Then run:

```powershell
python app.py
```

## Verification checklist

1. Existing chats are still visible.
2. Existing chat documents remain attached.
3. Global documents remain available.
4. Normal RAG answers work.
5. OCR uploads work.
6. Three-option mode works.
7. Light and dark themes work.
8. The system-status panel reports component states.
9. `python -m pytest` reports 11 passing tests.
10. Deleting a chat removes its physical chat-document files.
11. Waitress starts without Flask's development-server warning.
