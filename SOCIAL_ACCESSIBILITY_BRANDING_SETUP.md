# Social Source Reliability, Light Theme Accessibility, and Neon Branding

This release improves the social-source workflow and visual clarity without changing the database schema.

## What changed

### Social-source fallback

AI Studio still respects `robots.txt` and platform access rules. When LinkedIn, Facebook, Instagram, or another platform blocks automatic reading, the interface now:

1. Opens the manual fallback automatically.
2. Explains why the automatic import failed.
3. Focuses the visible-content text box.
4. Keeps the original social URL as the citation.
5. Provides a separate **Index pasted content** action.

No social-media password is requested or stored.

### Light-theme accessibility

The light theme now provides stronger contrast for:

- Primary and secondary buttons
- Disabled buttons
- Knowledge tabs
- Drawer controls
- Upload and indexing fields
- Refresh and delete actions
- Success, working, and error messages
- Social, website, and document cards

### Neon title

The main **AI Assistant** title now uses a modern cyan, blue, and violet neon gradient. A darker accessible gradient is used in light mode.

## Installation

Stop AI Studio before copying the update.

```powershell
Ctrl + C
```

Copy the extracted package over the project while preserving local data:

```powershell
$source = "$env:USERPROFILE\Downloads\ai_studio_social_accessibility_branding"
$project = "C:\Users\islam\PythonProject\AI-Chat-App"

robocopy $source $project /E `
  /XD .venv venv uploads logs .git .idea __pycache__ .pytest_cache `
  /XF .env .env.docker *.pyc
```

No dependency or database migration change is required.

## Validation

```powershell
cd "C:\Users\islam\PythonProject\AI-Chat-App"
python -m compileall -q .
python -m pytest
```

Expected:

```text
55 passed
```

Optional JavaScript validation:

```powershell
Get-ChildItem static\js\*.js |
ForEach-Object {
    node --check $_.FullName
}
```

Start AI Studio:

```powershell
python app.py
```

Open `http://127.0.0.1:5000` and press `Ctrl + F5`.

## Testing a blocked social page

1. Open **Knowledge Sources → Manage → Global Library**.
2. Paste the social URL.
3. Click **Import public**.
4. When the platform blocks reading, confirm the fallback opens automatically.
5. Copy visible About, caption, description, or post text from the social page.
6. Paste it into **Visible social content**.
7. Optionally provide a source title.
8. Click **Index pasted content**.
9. Ask a question based on the pasted content.
10. Confirm the citation opens the original social URL.

Automatic import cannot bypass platform login restrictions or `robots.txt`. The manual workflow is the safe and reliable fallback for those pages.
