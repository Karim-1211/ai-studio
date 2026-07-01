# AI Studio Portfolio Release v1.4 — Setup Guide

This release improves the public GitHub presentation and documentation only.

It does **not** change application logic, database migrations, AI providers, or Render behavior.

## What this package updates

- README.md
- Documentation files in `docs/`
- RELEASE_NOTES.md
- CONTRIBUTING.md
- SECURITY.md
- LICENSE
- Portfolio, resume, LinkedIn, and interview materials

## What this package does NOT change

- Python backend logic
- Database schema
- Render secrets
- Gemini configuration
- Ollama local mode configuration
- Existing working RAG pipeline

---

## Step 1 — Open VS Code

Open your working project folder:

```powershell
C:\Users\islam\Downloads\AI-Chat-App-phase4-multi-provider-render-ready\AI-Chat-App
```

Open a new terminal in VS Code.

---

## Step 2 — Locate the ZIP

```powershell
$zip = "$env:USERPROFILE\Downloads\ai_studio_portfolio_release_v1_4.zip"
Test-Path $zip
```

Expected:

```text
True
```

---

## Step 3 — Extract the package

```powershell
$source = "$env:USERPROFILE\Downloads\ai_studio_portfolio_release_v1_4"

Remove-Item $source -Recurse -Force -ErrorAction SilentlyContinue

Expand-Archive -Path $zip -DestinationPath $source -Force
```

---

## Step 4 — Verify extracted files

```powershell
Test-Path "$source\README.md"
Test-Path "$source\DUAL_MODE_PORTFOLIO_V1_4_SETUP.md"
Test-Path "$source\docs\03-Architecture.md"
Test-Path "$source\RELEASE_NOTES.md"
```

Expected:

```text
True
True
True
True
```

---

## Step 5 — Copy into project

```powershell
$project = "C:\Users\islam\Downloads\AI-Chat-App-phase4-multi-provider-render-ready\AI-Chat-App"

robocopy $source $project /E `
  /XD .venv venv uploads logs .git .idea __pycache__ .pytest_cache `
  /XF .env .env.docker *.pyc
```

At the end, confirm:

```text
FAILED    0
```

---

## Step 6 — Validate

Because this release is documentation-only, Python code should not change. Still run:

```powershell
cd $project
python -m compileall -q .
git status
```

Expected:

- `compileall` gives no output.
- `git status` shows documentation changes.

---

## Step 7 — Commit and push

```powershell
git add .
git commit -m "Release AI Studio Portfolio v1.4"
git push origin main
```

---

## Step 8 — Verify GitHub

Open:

```text
https://github.com/Karim-1211/ai-studio
```

Check:

- README looks professional.
- Docs folder is visible.
- Release notes are visible.
- Live demo link should be updated manually if needed.

---

## Step 9 — Render impact

Render may redeploy because GitHub changed, but this release does not change runtime logic.

After deployment, quickly test:

1. Login
2. Normal chat
3. One knowledge upload
4. Health status

Expected: all continue working as before.

---

## Rollback

If you do not like the documentation update:

```powershell
git log --oneline -5
git revert <commit-id>
git push origin main
```

Replace `<commit-id>` with the commit created for v1.4.
