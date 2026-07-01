# AI Studio Cloud Edition v1.2 Setup Guide

This release is for the Render + Neon PostgreSQL + Gemini deployment.

## What this release fixes

- Replaces the Ollama-only embedding service with a Gemini/Ollama-aware embedding service.
- Uses Gemini embeddings in cloud mode: `gemini-embedding-001`.
- Keeps Ollama embeddings available only for local mode.
- Fixes health status so Gemini cloud deployments show Ready.
- Fixes first-owner browser setup for Render Free deployments.
- Fixes attachment upload processing for PDF, DOCX, TXT, PNG, JPG, JPEG, and WebP.
- Keeps image uploads available for Gemini direct image analysis.
- Updates Render Blueprint config for an existing external database such as Neon.
- No database migration is required.

## Important before starting

Use the GitHub/Render project folder, not your old PyCharm local folder.

Correct folder:

```powershell
C:\Users\islam\Downloads\AI-Chat-App-phase4-multi-provider-render-ready\AI-Chat-App
```

Do not use:

```powershell
C:\Users\islam\PythonProject\AI-Chat-App
```

## Step 1 — Open VS Code terminal

Open VS Code in:

```powershell
C:\Users\islam\Downloads\AI-Chat-App-phase4-multi-provider-render-ready\AI-Chat-App
```

Your terminal prompt should look similar to:

```powershell
PS C:\Users\islam\Downloads\AI-Chat-App-phase4-multi-provider-render-ready\AI-Chat-App>
```

## Step 2 — Locate the ZIP

```powershell
$zip = "$env:USERPROFILE\Downloads\ai_studio_cloud_edition_v1_2.zip"
Test-Path $zip
```

Expected:

```powershell
True
```

If it says `False`, make sure the ZIP is downloaded into your Downloads folder.

## Step 3 — Extract the ZIP

```powershell
$source = "$env:USERPROFILE\Downloads\ai_studio_cloud_edition_v1_2"
Remove-Item $source -Recurse -Force -ErrorAction SilentlyContinue
Expand-Archive -Path $zip -DestinationPath $source -Force
```

## Step 4 — Verify extracted files

```powershell
Test-Path "$source\CLOUD_EDITION_V1_2_SETUP.md"
Test-Path "$source\CLOUD_EDITION_V1_2_VALIDATION_REPORT.md"
Test-Path "$source\services\embedding_service.py"
Test-Path "$source\routes\attachment_routes.py"
```

Expected:

```powershell
True
True
True
True
```

If any value is `False`, stop and send the terminal output.

## Step 5 — Set your project path

```powershell
$project = "C:\Users\islam\Downloads\AI-Chat-App-phase4-multi-provider-render-ready\AI-Chat-App"
Test-Path "$project\app.py"
Test-Path "$project\render.yaml"
Test-Path "$project\.git"
```

Expected:

```powershell
True
True
True
```

If `.git` is `False`, you are in the wrong project folder.

## Step 6 — Copy the release into the project

```powershell
robocopy $source $project /E `
  /XD .venv venv uploads logs .git .idea __pycache__ .pytest_cache `
  /XF .env .env.docker *.pyc
```

At the bottom, confirm:

```text
FAILED    0
```

Robocopy exit codes 0, 1, 2, or 3 are usually okay. The important thing is `FAILED 0`.

## Step 7 — Validate Python syntax

```powershell
cd $project
python -m compileall -q .
```

Expected: no output.

Then run these individual checks:

```powershell
python -m py_compile services/embedding_service.py
python -m py_compile services/health_service.py
python -m py_compile routes/auth_routes.py
python -m py_compile routes/attachment_routes.py
python -m py_compile routes/document_routes.py
python -m py_compile routes/global_document_routes.py
python -m py_compile routes/website_routes.py
python -m py_compile routes/social_routes.py
python -m py_compile routes/chat_routes.py
```

Expected: no output.

If you see an error, stop and send the full terminal output.

## Step 8 — Check Git changes

```powershell
git status
```

You should see modified files.

## Step 9 — Commit and push

```powershell
git add .
git commit -m "Release AI Studio Cloud Edition v1.2"
git push origin main
```

## Step 10 — Verify Render environment variables

Go to Render → `ai-studio` → Environment.

Make sure these are set exactly:

```text
AI_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash
GEMINI_MODELS=gemini-2.5-flash,gemini-1.5-flash
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=gemini-embedding-001
GEMINI_EMBEDDING_DIMENSIONS=768
```

Also make sure these exist and are not empty:

```text
GEMINI_API_KEY=your Google AI Studio API key
DATABASE_URL=your Neon PostgreSQL connection string
```

Important: remove or replace old values like:

```text
EMBEDDING_MODEL=embeddinggemma
EMBEDDING_MODEL=text-embedding-004
```

They must not remain active in Render.

## Step 11 — Redeploy on Render

Render should redeploy automatically after your Git push.

If not:

```text
Render → ai-studio → Manual Deploy → Deploy latest commit
```

Wait until Render shows `Live`.

## Step 12 — Clean old failed records in the UI

Old failed documents will not repair automatically.

In AI Studio:

1. Open Manage Knowledge.
2. Delete failed global documents using the trash icon.
3. Delete failed website/social records if any.
4. Start fresh tests below.

## Step 13 — Test in this exact order

### Test 1 — Normal chat

Ask:

```text
Hello, are you working?
```

Expected: Gemini replies.

### Test 2 — TXT attachment

1. Click `+ New Chat`.
2. Upload one small `.txt` file.
3. Ask:

```text
Summarize this file.
```

Expected: the answer uses the file content.

### Test 3 — PDF attachment

1. Click `+ New Chat`.
2. Upload one readable PDF, preferably text-based and small.
3. Ask:

```text
What is this PDF about?
```

Expected: the answer uses the PDF content.

### Test 4 — DOCX attachment

1. Click `+ New Chat`.
2. Upload one DOCX.
3. Ask:

```text
Summarize this document.
```

Expected: the answer uses the DOCX content.

### Test 5 — Image attachment

1. Click `+ New Chat`.
2. Upload one clear PNG or JPG.
3. Ask:

```text
Describe this image.
```

Expected: Gemini analyzes the image. If OCR finds text, the answer may use OCR too.

### Test 6 — Global library upload

1. Manage Knowledge → Global library.
2. Upload one small TXT or PDF.
3. Wait until it says Ready.
4. Select it.
5. Turn `Use knowledge` ON.
6. Ask a question from that file.

Expected: answer uses global knowledge.

### Test 7 — Website knowledge

1. Manage Knowledge → Global library.
2. Add one page, not 25 at first.
3. Wait until indexed.
4. Select it.
5. Turn `Use knowledge` ON.
6. Ask a question from that website.

Expected: answer uses website knowledge.

### Test 8 — Social knowledge

Instagram often blocks automatic scraping. This is normal.

Use manual fallback:

1. Open the Instagram page yourself.
2. Copy visible profile/about/caption text.
3. Paste it into `Visible social content`.
4. Click `Index pasted content`.
5. Ask a question from that pasted content.

Expected: manual social knowledge works.

## If anything fails

Send exactly these two things:

1. Browser Network error response for the failed request.
2. Render logs from the same time.

Do not make manual code changes before sending the logs.
