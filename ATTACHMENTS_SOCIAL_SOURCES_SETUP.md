# Chat Attachments and Social Sources Setup

This release adds ChatGPT-style message attachments and reusable social-media knowledge sources without removing any existing chats, files, websites, OCR data, or settings.

## Features

### Chat attachments

- Attach from the paperclip button beside the prompt.
- Drag files onto the composer.
- Paste screenshots from the clipboard.
- Supported formats: PDF, DOCX, TXT, PNG, JPG, JPEG, and WebP.
- Up to five attachments per message by default.
- PDFs and documents use the existing extraction, OCR, chunking, and embedding pipeline.
- Images are sent directly to the selected Ollama model when it supports vision.
- When the selected model is text-only, AI Studio automatically searches installed models for a vision-capable fallback and passes the visual analysis to the selected model.
- Attachments remain visible when the saved chat is reopened.
- Attachment files are removed when their chat is deleted.

### Social knowledge sources

- Supports Facebook, Instagram, X/Twitter, TikTok, LinkedIn, YouTube, Threads, and Bluesky URLs.
- Publicly readable pages are indexed on a best-effort basis.
- When a platform requires login or blocks automated reading, paste the visible caption, About text, description, or post content in the optional text field.
- The original social URL remains the citation.
- Social sources can be selected, refreshed when automatically extracted, cited, and deleted.
- Pasted sources cannot be refreshed automatically; delete and add the updated text again.

This release does not request social-media passwords and does not include OAuth account synchronization. Platform APIs and permissions are separate integrations.

## Install the update

### 1. Stop AI Studio

```powershell
Ctrl + C
```

### 2. Copy the extracted package into the project

```powershell
$source = "$env:USERPROFILE\Downloads\ai_studio_attachment_social_sources"
$project = "C:\Users\islam\PythonProject\AI-Chat-App"

Test-Path $source
```

The result must be `True`.

```powershell
robocopy $source $project /E `
  /XD .venv venv uploads logs .git .idea __pycache__ .pytest_cache `
  /XF .env .env.docker *.pyc
```

Confirm that the Robocopy summary shows `FAILED 0`.

### 3. Install dependencies

```powershell
cd "C:\Users\islam\PythonProject\AI-Chat-App"
python -m pip install -r requirements-dev.txt
```

### 4. Add optional settings to `.env`

```env
# Leave blank to auto-detect an installed Ollama vision model.
VISION_MODEL=

MAX_CONTENT_LENGTH=26214400
ATTACHMENT_MAX_FILES=5
ATTACHMENT_MAX_FILE_BYTES=20971520
ATTACHMENT_MAX_TOTAL_BYTES=41943040

SOCIAL_MAX_MANUAL_CHARACTERS=200000
SOCIAL_MIN_TEXT_CHARACTERS=40
```

For predictable image analysis, set `VISION_MODEL` to an installed vision-capable model. Example:

```powershell
ollama pull gemma3:4b
```

Then set:

```env
VISION_MODEL=gemma3:4b
```

AI Studio also auto-detects a vision-capable installed model when this setting is blank.

### 5. Apply the database migration

```powershell
python -m flask --app app:create_app db upgrade
python -m flask --app app:create_app db current
```

Expected migration:

```text
20260628_0003 (head)
```

Do not use `db stamp head` for this update. The migration must create the attachment and social-source tables.

### 6. Validate

```powershell
python -m compileall -q .
python -m pytest
```

Expected:

```text
27 passed
```

Optional JavaScript validation when Node.js is installed:

```powershell
Get-ChildItem static\js\*.js | ForEach-Object { node --check $_.FullName }
```

### 7. Start AI Studio

```powershell
python app.py
```

Open `http://127.0.0.1:5000` and press `Ctrl + F5`.

## Test chat attachments

1. Create or open a chat.
2. Click the paperclip beside the prompt.
3. Select a screenshot or PDF.
4. Wait until the attachment chip says it is ready.
5. Ask a question about the attachment and send it.
6. Reopen the chat and confirm the attachment remains visible.
7. Test drag-and-drop and clipboard screenshot paste.

For visual questions, confirm an installed Ollama model reports vision capability. A text-only model can still use OCR-extracted text, but it cannot understand visual layout, objects, or charts without the vision fallback.

## Test social sources

1. Open **Knowledge Sources → Manage → Global Library**.
2. Find **Social sources**.
3. Add a complete supported public URL.
4. Wait for indexing and ensure its checkbox is selected.
5. Ask a question based on that source.
6. Confirm the citation opens the original social URL.
7. Test refresh and delete.

When the public URL cannot be read:

1. Expand **Page requires login? Paste its visible text**.
2. Enter an optional title.
3. Paste the visible post, caption, About section, or description.
4. Add the source again.

Only add content you are permitted to store and use.
