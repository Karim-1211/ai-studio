# Cloud Deployment Guide

AI Studio cloud mode is designed for Render + Neon PostgreSQL + Gemini.

## Required Environment Variables

```env
APP_ENV=production
AI_PROVIDER=gemini
EMBEDDING_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash
EMBEDDING_MODEL=gemini-embedding-001
DATABASE_URL=<Neon PostgreSQL URL>
GEMINI_API_KEY=<Gemini API key>
AUTH_REQUIRED=true
```

## Deployment Steps

1. Push code to GitHub.
2. Connect GitHub repo to Render.
3. Add environment variables.
4. Deploy latest commit.
5. Verify `/api/health`.
6. Test chat, uploads, and knowledge search.
