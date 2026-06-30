# Complete Attachments, Social Sources, and Voice Chat Setup

This package replaces the earlier Chat Attachments + Social Knowledge Sources package and includes the new Voice Chat feature. Install this package directly over the project version that was used to create `AI-Chat-App-crawler-phase.zip`.

## Included features

- Chat-box file attachments
- Drag-and-drop and clipboard screenshot paste
- PDF/document OCR and RAG
- Vision-capable Ollama image analysis
- Social links in the Global Knowledge Library
- Manual pasted-text fallback for blocked social pages
- Microphone speech-to-text
- Automatic assistant read-aloud
- Read-aloud buttons on responses and option cards

## Installation

1. Stop Flask with `Ctrl + C`.
2. Extract the package.
3. Copy it over the project while preserving `.env`, uploads, logs, `.venv`, and Git data.
4. Install development requirements.
5. Configure an optional vision model.
6. Apply database migration `20260628_0003`.
7. Run tests.
8. Start AI Studio and hard-refresh the browser.

### PowerShell copy

```powershell
$source = "$env:USERPROFILE\Downloads\ai_studio_attachment_social_voice"
$project = "C:\Users\islam\PythonProject\AI-Chat-App"

robocopy $source $project /E `
  /XD .venv venv uploads logs .git .idea __pycache__ .pytest_cache `
  /XF .env .env.docker *.pyc
```

Confirm the Robocopy summary shows `FAILED 0`.

### Dependencies

```powershell
cd "C:\Users\islam\PythonProject\AI-Chat-App"
python -m pip install -r requirements-dev.txt
```

### Optional vision model

```powershell
ollama pull gemma3:4b
```

Add to `.env`:

```env
VISION_MODEL=gemma3:4b
```

### Database migration

```powershell
python -m flask --app app:create_app db upgrade
python -m flask --app app:create_app db current
```

Expected migration head:

```text
20260628_0003 (head)
```

Do not use `db stamp head` for this update. The migration must create the attachment and social-source tables.

### Validation

```powershell
python -m compileall -q .
python -m pytest
Get-ChildItem static\js\*.js | ForEach-Object { node --check $_.FullName }
```

Expected automated result:

```text
30 passed
```

### Start

```powershell
python app.py
```

Open `http://127.0.0.1:5000` and press `Ctrl + F5`.

## Voice browser note

Voice input works best in current Microsoft Edge or Google Chrome. Microphone permission works on localhost. A deployed site normally needs HTTPS. Depending on the browser, speech recognition may use the browser vendor's service; audio is not uploaded to the Flask backend by this implementation.
