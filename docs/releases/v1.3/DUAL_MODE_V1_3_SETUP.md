# AI Studio Dual Mode v1.3 Setup

This release keeps your live Render/Gemini app safe while adding a clear local Ollama mode.

## What this release adds

- `.env.local.example` for local Ollama mode
- `.env.cloud.example` for Render/Gemini reference
- clearer environment examples
- beginner-safe local Ollama setup guide
- validation and rollback guide

## What this release does not change

- No database migration
- No change to your Render DATABASE_URL
- No change to your Render GEMINI_API_KEY
- No UI redesign
- No reset of your production data

## Step 1 - Download and locate the ZIP

```powershell
$zip = "$env:USERPROFILE\Downloads\ai_studio_dual_mode_v1_3.zip"
Test-Path $zip
```

Expected:

```text
True
```

## Step 2 - Extract the ZIP

```powershell
$source = "$env:USERPROFILE\Downloads\ai_studio_dual_mode_v1_3"
Remove-Item $source -Recurse -Force -ErrorAction SilentlyContinue
Expand-Archive -Path $zip -DestinationPath $source -Force
```

Verify:

```powershell
Test-Path "$source\DUAL_MODE_V1_3_SETUP.md"
Test-Path "$source\LOCAL_OLLAMA_MODE_SETUP.md"
Test-Path "$source\.env.local.example"
Test-Path "$source\.env.cloud.example"
```

Expected all True.

## Step 3 - Copy package into your project

```powershell
$project = "C:\Users\islam\Downloads\AI-Chat-App-phase4-multi-provider-render-ready\AI-Chat-App"

robocopy $source $project /E `
  /XD .venv venv uploads logs .git .idea __pycache__ .pytest_cache `
  /XF .env .env.docker *.pyc
```

At the bottom, confirm:

```text
FAILED    0
```

## Step 4 - Validate locally

```powershell
cd $project
python -m compileall -q .
python -m py_compile config.py
python -m py_compile services/ai_provider_service.py
python -m py_compile services/embedding_service.py
python -m py_compile services/health_service.py
python -m py_compile routes/model_routes.py
```

Expected: no output.

## Step 5 - Commit and push

```powershell
git status
git add .
git commit -m "Release AI Studio Dual Mode v1.3"
git push origin main
```

## Step 6 - Render check

Render should redeploy automatically. After it is live, confirm these environment variables remain set:

```text
AI_PROVIDER=gemini
EMBEDDING_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash
EMBEDDING_MODEL=gemini-embedding-001
DATABASE_URL=<your Neon URL>
GEMINI_API_KEY=<your Gemini key>
```

Do not set Render to Ollama.

## Step 7 - Cloud smoke test

On the live Render app:

1. Send a chat message.
2. Upload a TXT file.
3. Upload a PDF or DOCX.
4. Test Manage Knowledge.
5. Test website indexing.
6. Confirm status is Ready.

## Step 8 - Optional local Ollama test

Follow `LOCAL_OLLAMA_MODE_SETUP.md`.
