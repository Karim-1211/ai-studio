# AI Studio Professional Edition v2.0 — Validation Guide

## Local validation

Run:

```powershell
python -m compileall -q .
node --check static/js/chat.js
node --check static/js/app.js
```

Expected: no errors.

## Browser validation

- Normal Gemini chat works.
- Streaming shows tokens progressively.
- Stop button stops generation.
- Partial stopped answer remains visible.
- Partial stopped answer is saved to chat history.
- RAG/attachments still work.
- Website knowledge still works.
- Local Ollama mode is not changed by this release.

## Render validation

- Deploy succeeds.
- `/api/health` returns ready/degraded but not unavailable.
- Chat request returns 200.
