# Admin Dashboard, Reliability, Accessibility, and Security setup

This phase adds the administrator dashboard, usage analytics, model timing, failed-request history, sampled health history, audit logs, cleanup tools, rate limiting, accessibility improvements, stronger light-theme contrast, and collapsible RAG source lists.

## Database migration

Expected previous revision:

```text
20260628_0006 (head)
```

Apply:

```powershell
python -m flask --app app:create_app db upgrade
```

Expected new revision:

```text
20260628_0007 (head)
```

Do not use `db stamp` for this phase.

## Admin dashboard

Sign in as an administrator, open the account menu, and choose **Admin dashboard**.

The dashboard shows:

- Active and disabled accounts
- Chats and messages per user
- Per-user file and attachment storage
- Website and social-source counts
- Model request counts and average generation duration
- Recent failed requests
- Sampled system-health history
- Audit events
- Orphan-upload cleanup
- Telemetry-retention cleanup

Analytics begin collecting after this phase is installed. Historical chats still appear in user totals, while historical model timing is not reconstructed.

## Recommended environment settings

```env
METRICS_ENABLED=true
HEALTH_HISTORY_INTERVAL_SECONDS=300
RATE_LIMIT_ENABLED=true
RATE_LIMIT_CHAT_PER_MINUTE=30
RATE_LIMIT_API_PER_MINUTE=120
RATE_LIMIT_UPLOADS_PER_10_MINUTES=20
RATE_LIMIT_LOGIN_ATTEMPTS=10
RATE_LIMIT_LOGIN_WINDOW_SECONDS=900
```

## Collapsible sources

RAG citations are collapsed by default. Click the compact source summary to expand the full list. The open or closed state is remembered for the browser session.

## Browser tests

See `docs/TESTING_AND_ACCESSIBILITY.md` and `requirements-e2e.txt`.

## Backup rehearsal

See `docs/BACKUP_RESTORE_REHEARSAL.md` before the final deployment phase.
