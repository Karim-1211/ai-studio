# AI Studio Portfolio v1.4 — Validation Guide

This release is documentation and portfolio focused.

## Local validation

```powershell
python -m compileall -q .
git status
```

Expected:

- No Python compilation errors.
- Only documentation/metadata files changed.

## GitHub validation

After push, verify:

- README renders correctly.
- Docs links work.
- Live demo URL is visible.
- LinkedIn/GitHub links are correct.

## Live app validation

After Render redeploys, test:

1. Login
2. Ask a Gemini chat question
3. Upload one small TXT or PDF
4. Use knowledge search
5. Open `/api/health`

Expected:

- App remains live.
- Ready status remains green.
- No runtime regression.
