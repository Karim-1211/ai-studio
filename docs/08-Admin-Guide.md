# Admin Guide

Admins manage users, health, usage, and system status.

## First Owner

On a new database, create the first owner from the browser setup flow.

## Health Monitoring

Open:

```text
/api/health
```

Check provider status, database, OCR, uploads, and embeddings.

## Production Safety

Never commit `.env` or API keys to GitHub.
