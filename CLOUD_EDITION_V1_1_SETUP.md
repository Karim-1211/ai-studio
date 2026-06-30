# AI Studio Cloud Edition v1.1 — Gemini Knowledge/RAG Stabilization

This release fixes the Gemini cloud knowledge pipeline after the Ollama-to-Gemini migration.

## What this release fixes

- Uses Gemini for embeddings in cloud mode.
- Removes the Render/Ollama embedding dependency for RAG.
- Sets Render defaults to:
  - `AI_PROVIDER=gemini`
  - `GEMINI_MODEL=gemini-2.5-flash`
  - `EMBEDDING_PROVIDER=gemini`
  - `EMBEDDING_MODEL=gemini-embedding-001`
- Keeps Ollama embedding support available for local mode.
- Updates health status so cloud mode checks Gemini configuration instead of Ollama.
- Keeps the existing database schema unchanged.

## Important Render environment values

After pushing this release, verify these in Render → ai-studio → Environment:

```text
AI_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash
GEMINI_MODELS=gemini-2.5-flash
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=gemini-embedding-001
GEMINI_API_KEY=<your Google AI Studio key>
DATABASE_URL=<your Neon PostgreSQL connection string>
```

Remove or replace old values such as:

```text
EMBEDDING_MODEL=embeddinggemma
EMBEDDING_MODEL=text-embedding-004
```

## Install steps

Run these from PowerShell.

### 1. Locate the ZIP

```powershell
$zip = "$env:USERPROFILE\Downloads\ai_studio_cloud_edition_v1_1.zip"
Test-Path $zip
```

Expected:

```text
True
```

### 2. Extract the ZIP

```powershell
$source = "$env:USERPROFILE\Downloads\ai_studio_cloud_edition_v1_1"
Remove-Item $source -Recurse -Force -ErrorAction SilentlyContinue
Expand-Archive -Path $zip -DestinationPath $source -Force
```

Verify:

```powershell
Test-Path "$source\CLOUD_EDITION_V1_1_SETUP.md"
Test-Path "$source\services\embedding_service.py"
Test-Path "$source\services\health_service.py"
```

All should return:

```text
True
```

### 3. Copy the release into your GitHub/Render project folder

Use your deployment project folder, not the old PyCharm folder:

```powershell
$project = "C:\Users\islam\Downloads\AI-Chat-App-phase4-multi-provider-render-ready\AI-Chat-App"

robocopy $source $project /E `
  /XD .venv venv uploads logs .git .idea __pycache__ .pytest_cache `
  /XF .env .env.docker *.pyc
```

Confirm:

```text
FAILED    0
```

### 4. Run validation locally

```powershell
cd $project

python -m compileall -q .
python -m py_compile services/embedding_service.py
python -m py_compile services/health_service.py
python -m py_compile routes/attachment_routes.py
python -m py_compile routes/document_routes.py
python -m py_compile routes/global_document_routes.py
python -m py_compile routes/website_routes.py
python -m py_compile routes/social_routes.py
```

Expected: no output.

### 5. Commit and push

```powershell
git status
git add .
git commit -m "Release AI Studio Cloud Edition v1.1"
git push origin main
```

### 6. Render deployment

Render should redeploy automatically.

If not:

```text
Render → ai-studio → Manual Deploy → Deploy latest commit
```

### 7. Update Render environment variables

In Render → ai-studio → Environment, confirm these values:

```text
AI_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash
GEMINI_MODELS=gemini-2.5-flash
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=gemini-embedding-001
GEMINI_API_KEY=<your key>
DATABASE_URL=<your Neon URL>
```

Save changes and redeploy if you changed anything.

### 8. Clean failed old records

Old failed records created with `embeddinggemma` or `text-embedding-004` will not repair automatically.

In the app:

- Delete failed global files using the trash icon.
- Delete failed website pages if any appear.
- Re-upload/re-index them after this deployment is live.

### 9. Test order after deploy

Test in this exact order:

1. Normal chat: `Hello, are you working?`
2. Upload a small TXT attachment and ask: `Summarize this file.`
3. Upload a PDF attachment and ask a direct question from the PDF.
4. Upload a DOCX attachment and ask a direct question from the DOCX.
5. Upload an image and ask what is visible.
6. Manage Knowledge → Global Library → upload a small TXT or PDF.
7. Turn on `Use knowledge`.
8. Ask a question from the global file.
9. Manage Knowledge → Add website page.
10. Ask a question from the indexed website.
11. Social source: for Instagram, use the manual paste fallback because Instagram blocks automated scraping.

## Notes

- No database migration is required.
- This release does not require Render Shell.
- This release does not require Ollama on Render.
- Ollama remains available for local development if you set `AI_PROVIDER=ollama` and `EMBEDDING_PROVIDER=ollama` locally.
