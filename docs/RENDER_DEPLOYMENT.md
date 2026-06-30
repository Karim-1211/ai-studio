# Render Deployment Guide

This project is designed for a hybrid AI setup:

- **Local development:** `AI_PROVIDER=ollama`, using local Ollama models.
- **Public portfolio demo:** `AI_PROVIDER=gemini`, using a hosted API so clients can chat online without installing Ollama.

## 1. Prepare GitHub

1. Commit the cleaned project to GitHub.
2. Do not commit `.env`, `.env.docker`, logs, cache folders, or uploaded private files.
3. Keep `.env.example` and `.env.docker.example` as templates only.

## 2. Create Render services

Recommended method: use `render.yaml` as a Render Blueprint.

1. In Render, choose **New +** → **Blueprint**.
2. Connect the GitHub repository.
3. Render will create:
   - a Docker web service
   - a PostgreSQL database
4. Add the secret environment variable:
   - `GEMINI_API_KEY`

## 3. Required production variables

For the public demo:

```env
APP_ENV=production
AI_PROVIDER=gemini
GEMINI_API_KEY=your-real-key
GEMINI_MODEL=gemini-1.5-flash
DATABASE_URL=provided-by-render
SECRET_KEY=generated-or-strong-random-value
SESSION_COOKIE_SECURE=true
ENABLE_HSTS=true
TRUST_PROXY_HEADERS=true
RUN_MIGRATIONS=true
```

For local development:

```env
APP_ENV=development
AI_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434
DATABASE_URL=postgresql://postgres:password@localhost:5432/ai_studio_db
```

## 4. First admin account

After deployment, create your admin account using the existing project CLI command documented in the README/setup files. Then set `ALLOW_REGISTRATION=false` for the public demo.

## 5. Client demo checklist

Before sending the link to a client:

- Open the Render URL in an incognito browser.
- Log in with a demo account, not your private admin account.
- Send a normal chat prompt and confirm streaming works.
- Upload a small TXT or PDF and test RAG.
- Test mobile width in browser dev tools.
- Confirm `/api/health/live` returns healthy.
- Confirm no debug toolbar, stack traces, secrets, or local paths are visible.

## 6. Notes about Ollama

Ollama support remains in the codebase. It is not used by the public Render demo unless you set `AI_PROVIDER=ollama`. Public users should use the hosted provider because they cannot access Ollama running on your computer.


## Alternative AI providers

You can switch the deployed demo by changing `AI_PROVIDER` and adding the matching API key. Supported hosted providers are `openai`, `openrouter`, `gemini`, and `anthropic`. Local development can still use `ollama`.
