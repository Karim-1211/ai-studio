# AI Studio Cloud Edition v1.0 — Setup Guide

This release stabilizes AI Studio for the cloud deployment path:

- Render Web Service
- Neon PostgreSQL
- Gemini chat provider
- Gemini embeddings for RAG and knowledge search
- No Ollama dependency in cloud mode
- PDF, DOCX, TXT, image uploads
- Website and social knowledge indexing
- OCR with Tesseract in Docker
- Ready health status
- Browser first-owner setup

## What changed

### Cloud provider and embeddings
- Gemini is the default live-demo provider.
- `EMBEDDING_PROVIDER=gemini` is now supported.
- `EMBEDDING_MODEL=text-embedding-004` is used for cloud RAG.
- Ollama remains available for local mode, but Render no longer needs Ollama.

### Attachments and knowledge
- Message attachments now use the configured embedding provider.
- PDF, DOCX, TXT, and OCR image uploads no longer try to use Ollama when deployed with Gemini.
- Global documents, website sources, and social sources use Gemini embeddings.
- Image previews remain available for uploaded image attachments.

### Health and first setup
- Health status checks Gemini + Gemini embeddings instead of Ollama in cloud mode.
- A first administrator can be created from the browser when the database is empty.

### Render configuration
- `render.yaml` is configured for one Render web service only.
- `DATABASE_URL` is provided manually, so it works with Neon PostgreSQL and does not try to create a second Render free database.

---

## 1. Stop editing other copies

Only use your GitHub/Render project folder:

```powershell
C:\Users\islam\Downloads\AI-Chat-App-phase4-multi-provider-render-ready\AI-Chat-App
```

Do not use:

```powershell
C:\Users\islam\PythonProject\AI-Chat-App
```

for this Render deployment.

---

## 2. Download and locate the ZIP

After downloading this package, run:

```powershell
$zip = Get-ChildItem "$env:USERPROFILE\Downloads" `
  -Filter "*cloud*edition*v1*.zip" |
Sort-Object LastWriteTime -Descending |
Select-Object -First 1 -ExpandProperty FullName

$zip
Test-Path $zip
```

Expected:

```powershell
True
```

---

## 3. Extract the package

```powershell
$source = "$env:USERPROFILE\Downloads\ai_studio_cloud_edition_v1"

Remove-Item $source -Recurse -Force -ErrorAction SilentlyContinue

Expand-Archive `
  -Path $zip `
  -DestinationPath $source `
  -Force

Test-Path "$source\CLOUD_EDITION_V1_SETUP.md"
Test-Path "$source\app.py"
Test-Path "$source\services\embedding_service.py"
Test-Path "$source\routes\attachment_routes.py"
```

Expected: all return `True`.

---

## 4. Copy into your GitHub/Render project

```powershell
$project = "C:\Users\islam\Downloads\AI-Chat-App-phase4-multi-provider-render-ready\AI-Chat-App"

robocopy $source $project /E `
  /XD .git .venv venv uploads logs .idea __pycache__ .pytest_cache `
  /XF .env .env.docker *.pyc
```

Confirm in the robocopy summary:

```text
FAILED    0
```

---

## 5. Validate locally before pushing

```powershell
cd $project

python -m compileall -q .
python -m py_compile config.py
python -m py_compile services\embedding_service.py
python -m py_compile services\health_service.py
python -m py_compile routes\auth_routes.py
python -m py_compile routes\attachment_routes.py
python -m py_compile routes\document_routes.py
python -m py_compile routes\global_document_routes.py
python -m py_compile routes\website_routes.py
python -m py_compile routes\social_routes.py
python -m py_compile routes\chat_routes.py
```

Expected: no output.

Optional, if all dependencies are installed locally:

```powershell
python -m pytest
```

---

## 6. Commit and push

```powershell
git status
git add .
git commit -m "Release AI Studio Cloud Edition v1.0"
git push origin main
```

Render should redeploy automatically.

If it does not:

```text
Render → ai-studio → Manual Deploy → Deploy latest commit
```

---

## 7. Render environment variables

In Render → `ai-studio` → Environment, confirm these exist:

```text
APP_ENV=production
AI_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash
GEMINI_MODELS=gemini-2.5-flash,gemini-1.5-flash
GEMINI_API_KEY=<your Google AI Studio key>
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=text-embedding-004
DATABASE_URL=<your Neon PostgreSQL connection string>
OCR_ENABLED=true
TESSERACT_CMD=/usr/bin/tesseract
```

Do not paste API keys into GitHub or chat.

---

## 8. Test after Render deploy

Use a brand-new chat for testing.

1. **Health**
   - Status should show `Ready`.

2. **Chat**
   - Ask: `Hello, are you working?`
   - Gemini should answer.

3. **TXT attachment**
   - Upload a small `.txt` file.
   - Ask a question from that file.

4. **PDF attachment**
   - Upload a small readable PDF.
   - Ask a question from the PDF.

5. **DOCX attachment**
   - Upload a simple Word file.
   - Ask a question from it.

6. **Image attachment**
   - Upload a clear image with visible text.
   - Ask: `What text is visible in this image?`

7. **Global knowledge**
   - Open Manage Knowledge.
   - Upload a small PDF/TXT/DOCX.
   - Select it and ask a question.

8. **Website knowledge**
   - Add a simple public webpage.
   - Ask a question from that page.

9. **Social knowledge**
   - Add a supported public social/link source.
   - Ask a question from it.

---

## 9. Known limits

- Render free services may sleep after inactivity.
- Neon free limits apply to database usage.
- Gemini free-tier limits apply to chat and embeddings.
- Very large PDFs/images may hit upload or OCR safety limits.
- Scanned PDFs and low-quality images depend on OCR quality.

---

## 10. Rollback

If the deployment breaks, go to GitHub and revert the release commit, or redeploy the previous Render commit.

Render:

```text
Deploys → previous successful deploy → Redeploy
```

Git:

```powershell
git log --oneline -5
git revert <release_commit_hash>
git push origin main
```
